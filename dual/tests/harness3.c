/* Host-side test of jni/psxlink.c against the x86_64 core build, with a mock JNIEnv. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
#include <sys/stat.h>
#include <jni.h>
int __android_log_vprint(int p, const char *t, const char *f, va_list ap){ if (p >= 5 || getenv("VERBOSE")) { fprintf(stderr,"[%s] ",t); vfprintf(stderr,f,ap); fputc('\n',stderr);} return 0; }
int __android_log_print(int p, const char *t, const char *f, ...){ va_list ap; va_start(ap,f); __android_log_vprint(p,t,f,ap); va_end(ap); return 0; }
#include "../app/jni/psxlink.c"

typedef struct { int len; void *data; } Arr;
typedef struct { void *p; jlong cap; } Buf;
static const char* JNICALL gsu(JNIEnv*e,jstring s,jboolean*c){ return (const char*)s; }
static void JNICALL rsu(JNIEnv*e,jstring s,const char*c){}
static void* JNICALL gdba(JNIEnv*e,jobject b){ return ((Buf*)b)->p; }
static jlong JNICALL gdbc(JNIEnv*e,jobject b){ return ((Buf*)b)->cap; }
static void JNICALL siar(JNIEnv*e,jintArray a,jsize s,jsize n,const jint*v){ memcpy((jint*)((Arr*)a)->data+s,v,n*4); }
static void JNICALL giar(JNIEnv*e,jintArray a,jsize s,jsize n,jint*v){ memcpy(v,(jint*)((Arr*)a)->data+s,n*4); }
static jsize JNICALL gal(JNIEnv*e,jarray a){ return ((Arr*)a)->len; }
static jshort* JNICALL gsae(JNIEnv*e,jshortArray a,jboolean*c){ return ((Arr*)a)->data; }
static void JNICALL rsae(JNIEnv*e,jshortArray a,jshort*p,jint m){}
static jbyteArray JNICALL nba(JNIEnv*e,jsize n){ Arr*a=malloc(sizeof(Arr)); a->len=n; a->data=calloc(1,n); return (jbyteArray)a; }
static void JNICALL sbar(JNIEnv*e,jbyteArray a,jsize s,jsize n,const jbyte*v){ memcpy((jbyte*)((Arr*)a)->data+s,v,n); }
static void JNICALL gbar(JNIEnv*e,jbyteArray a,jsize s,jsize n,jbyte*v){ memcpy(v,(jbyte*)((Arr*)a)->data+s,n); }
static jstring JNICALL nsu(JNIEnv*e,const char*s){ return (jstring)strdup(s); }

#define CHECK(c, ...) do { if (c) { printf("PASS  " __VA_ARGS__); printf("\n"); } else { printf("FAIL  " __VA_ARGS__); printf("\n"); fails++; } } while(0)
int main(int argc, char **argv) {
   struct JNINativeInterface_ fn; memset(&fn,0,sizeof fn);
   fn.GetStringUTFChars=gsu; fn.ReleaseStringUTFChars=rsu; fn.GetDirectBufferAddress=gdba; fn.GetDirectBufferCapacity=gdbc;
   fn.SetIntArrayRegion=siar; fn.GetIntArrayRegion=giar; fn.GetArrayLength=gal; fn.GetShortArrayElements=gsae;
   fn.ReleaseShortArrayElements=rsae; fn.NewByteArray=nba; fn.SetByteArrayRegion=sbar; fn.GetByteArrayRegion=gbar; fn.NewStringUTF=nsu;
   const struct JNINativeInterface_ *envp=&fn; JNIEnv *e=(JNIEnv*)&envp; jclass c=NULL; int fails=0;
   mkdir("sys",0755); mkdir("save",0755); remove("save/test.srm");
   J(init)(e,c,(jstring)"sys",(jstring)"save");
   J(setVariable)(e,c,(jstring)"pcsx_rearmed_bios",(jstring)"HLE");
   J(setVariable)(e,c,(jstring)"pcsx_rearmed_memcard1",(jstring)"libretro");
   J(setVariable)(e,c,(jstring)"pcsx_rearmed_memcard2",(jstring)"disabled");
   jboolean ok = J(loadGame)(e,c,(jstring)(argc>1?argv[1]:"test.exe"),(jstring)"save/test.srm",2);
   CHECK(ok,"loadGame");
   if(!ok) return 1;
   printf("      fps=%.3f rate=%.0f aspect=%.3f\n", J(fps)(e,c), J(sampleRate)(e,c), J(aspect)(e,c));
   static uint16_t fbm[2048*1024]; Buf fb={fbm,sizeof fbm}; jint seqv=0; Arr seq={1,&seqv};
   static short au[16384]; Arr aa={16384,au}; long samples=0; int frames_new=0, last=-1;
   for(int i=0;i<300;i++){ J(runFrame)(e,c); samples+=J(readAudio)(e,c,(jshortArray)&aa); jint wh=J(copyFrame)(e,c,(jobject)&fb,last,(jintArray)&seq); last=seqv; if(wh) frames_new++; }
   CHECK(samples > 300*735*2*0.9, "audio produced: %ld samples over 300 frames (expect ~%d)", samples, 300*735*2);
   jint wh=J(copyFrame)(e,c,(jobject)&fb,-1,(jintArray)&seq);
   int w=wh>>16,h=wh&0xffff; long red=0; for(int i=0;i<w*h;i++) if((fbm[i]>>11)>0 && (fbm[i]&0x7ff)==0) red++;
   CHECK(w==320 && h==240, "frame size %dx%d", w, h);
   CHECK(frames_new > 250, "new frames delivered: %d/300", frames_new);
   CHECK(red > w*h*0.9, "picture is the program's red fill: %ld/%d pixels (pixel0=0x%04x)", red, w*h, fbm[0]);
   Arr *r1=(Arr*)J(readRam)(e,c,(jint)0x80100000,8); uint32_t c1=*(uint32_t*)r1->data;
   J(runFrame)(e,c); Arr *r2=(Arr*)J(readRam)(e,c,(jint)0x00100000,8); uint32_t c2=*(uint32_t*)r2->data;
   CHECK(c1>0 && c2>c1, "RAM counter live via 0x80100000 / 0x00100000 mirrors: %u -> %u", c1, c2);
   Arr *rk=(Arr*)J(readRam)(e,c,(jint)0xA0100000,4); CHECK(rk && *(uint32_t*)rk->data>=c2, "KSEG1 mirror readable");
   CHECK(J(readRam)(e,c,(jint)0x1F800000,4)==NULL, "out-of-RAM address rejected");
   remove("save/s1.state");
   CHECK(J(saveState)(e,c,(jstring)"save/s1.state"), "saveState");
   Arr *rs=(Arr*)J(readRam)(e,c,(jint)0x80100000,4); uint32_t at=*(uint32_t*)rs->data;
   for(int i=0;i<60;i++) J(runFrame)(e,c);
   Arr *ra=(Arr*)J(readRam)(e,c,(jint)0x80100000,4); uint32_t later=*(uint32_t*)ra->data;
   CHECK(J(loadState)(e,c,(jstring)"save/s1.state"), "loadState");
   Arr *rb=(Arr*)J(readRam)(e,c,(jint)0x80100000,4); uint32_t back=*(uint32_t*)rb->data;
   CHECK(back==at && later>at, "state restores RAM: saved %u, ran to %u, restored %u", at, later, back);
   Arr wv={4,"\x44\x33\x22\x11"}; CHECK(J(writeRam)(e,c,(jint)0x80180000,(jbyteArray)&wv), "writeRam");
   Arr *rw=(Arr*)J(readRam)(e,c,(jint)0x80180000,4); CHECK(*(uint32_t*)rw->data==0x11223344, "writeRam readback 0x%08x", *(uint32_t*)rw->data);
   J(setButtons)(e,c,0,(1<<RETRO_DEVICE_ID_JOYPAD_START)); J(setAxes)(e,c,0,-30000,0,0,0); J(setStickDpad)(e,c,1,12000);
   CHECK(input_state_cb(0,RETRO_DEVICE_JOYPAD,0,RETRO_DEVICE_ID_JOYPAD_LEFT)==1, "stick->dpad left");
   CHECK(input_state_cb(0,RETRO_DEVICE_JOYPAD,0,RETRO_DEVICE_ID_JOYPAD_MASK)==((1<<3)|(1<<6)), "bitmask start+left");
   CHECK(input_state_cb(0,RETRO_DEVICE_ANALOG,0,0)==-30000, "analog X passthrough");
   for(int i=0;i<30;i++) J(runFrame)(e,c);
   jlong h1=J(memcardHash)(e,c);
   CHECK(J(saveMemcard)(e,c), "saveMemcard");
   struct stat st; CHECK(stat("save/test.srm",&st)==0 && st.st_size==131072, "memory card file 128KB (%ld)", (long)st.st_size);
   printf("      gameId='%s' discs=%d hash=%llx\n", (char*)J(gameId)(e,c), J(discCount)(e,c), (unsigned long long)h1);
   J(setCheat)(e,c,0,1,(jstring)"80180000 BEEF");
   J(runFrame)(e,c); J(runFrame)(e,c);
   Arr *rc=(Arr*)J(readRam)(e,c,(jint)0x80180000,2); CHECK(*(uint16_t*)rc->data==0xBEEF, "cheat/mod code applied: 0x%04x", *(uint16_t*)rc->data);
   { int n0=J(discCount)(e,c), i0=J(discIndex)(e,c); jint idx=J(appendDisc)(e,c,(jstring)"test.exe"); CHECK(idx==n0 && J(discCount)(e,c)==n0+1 && J(discIndex)(e,c)==i0, "appendDisc queues without switching (idx %d, count %d->%d, index %d->%d)", idx, n0, J(discCount)(e,c), i0, J(discIndex)(e,c)); }
   {
#include "cht_codes.h"
     for (int i=0;i<(int)(sizeof CHT/sizeof *CHT);i++) J(setCheat)(e,c,i,i!=35,(jstring)CHT[i]);
     for(int i=0;i<3;i++) J(runFrame)(e,c);
     Arr *p=(Arr*)J(readRam)(e,c,(jint)0x80017400,4); Arr *q=(Arr*)J(readRam)(e,c,(jint)0x80017F04,5);
     uint16_t *w=(uint16_t*)p->data; uint8_t *o=(uint8_t*)q->data;
     CHECK(w[0]==0x8001 && w[1]==0x3C02, "analog program written at 0x80017400: %04x %04x", w[0], w[1]);
     CHECK(o[0]==0x10 && o[1]==0x10 && o[2]==0x10 && o[3]==0 && o[4]==0x10, "option bytes 0x80017F04..08 = %02x %02x %02x %02x %02x (invert off)", o[0],o[1],o[2],o[3],o[4]);
     extern int padToggleAnalog(unsigned);
     J(setAnalogMode)(e,c,1); int a=padToggleAnalog(0); padToggleAnalog(0);
     J(setAnalogMode)(e,c,1); int b2=padToggleAnalog(0); padToggleAnalog(0);
     CHECK(a==0 && b2==0, "setAnalogMode(on) leaves the pad in analog mode, twice in a row (probe flips it to %d,%d)", a, b2);
     J(setAnalogMode)(e,c,0); int d=padToggleAnalog(0); padToggleAnalog(0);
     CHECK(d==1, "setAnalogMode(off) leaves it digital");
   }
   J(unload)(e,c);
   printf("%s (%d failures)\n", fails?"SOME TESTS FAILED":"ALL PASSED", fails);
   return fails!=0;
}
