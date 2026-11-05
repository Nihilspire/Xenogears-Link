/* Line-command driver around jni/psxlink.c for headless tests with the real game. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
#include <jni.h>
int __android_log_vprint(int p, const char *t, const char *f, va_list ap){ if (getenv("VERBOSE")) { fprintf(stderr,"[%s] ",t); vfprintf(stderr,f,ap); fputc('\n',stderr);} return 0; }
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
static jbyteArray JNICALL nba(JNIEnv*e,jsize n){ static Arr a; static char buf[1<<23]; if(n>(jsize)sizeof buf)return NULL; a.len=n; a.data=buf; return (jbyteArray)&a; }   /* 8 MB: a save state is ~4.4 MB */
static void JNICALL sbar(JNIEnv*e,jbyteArray a,jsize s,jsize n,const jbyte*v){ memcpy((jbyte*)((Arr*)a)->data+s,v,n); }
static void JNICALL gbar(JNIEnv*e,jbyteArray a,jsize s,jsize n,jbyte*v){ memcpy(v,(jbyte*)((Arr*)a)->data+s,n); }
static jstring JNICALL nsu(JNIEnv*e,const char*s){ static char b[16384]; snprintf(b,sizeof b,"%s",s); return (jstring)b; }
static uint16_t fb[2048*1024]; static short au[16384];
int main(void) {
   struct JNINativeInterface_ fn; memset(&fn,0,sizeof fn);
   fn.GetStringUTFChars=gsu; fn.ReleaseStringUTFChars=rsu; fn.GetDirectBufferAddress=gdba; fn.GetDirectBufferCapacity=gdbc;
   fn.SetIntArrayRegion=siar; fn.GetIntArrayRegion=giar; fn.GetArrayLength=gal; fn.GetShortArrayElements=gsae;
   fn.ReleaseShortArrayElements=rsae; fn.NewByteArray=nba; fn.SetByteArrayRegion=sbar; fn.GetByteArrayRegion=gbar; fn.NewStringUTF=nsu;
   const struct JNINativeInterface_ *envp=&fn; JNIEnv *e=(JNIEnv*)&envp; jclass c=NULL;
   char line[8192], a1[4096], a2[4096]; Buf b={fb,sizeof fb}; jint seqv=0; Arr seq={1,&seqv}; Arr aa={16384,au};
   setvbuf(stdout,NULL,_IOLBF,0);
   while (fgets(line,sizeof line,stdin)) {
      char cmd[32]={0}; long x=0,y=0,z=0,w=0; a1[0]=a2[0]=0;
      sscanf(line,"%31s",cmd);
      if (!strcmp(cmd,"init")) { sscanf(line,"%*s %s %s",a1,a2); J(init)(e,c,(jstring)a1,(jstring)a2); puts("ok"); }
      else if (!strcmp(cmd,"var")) { sscanf(line,"%*s %s %s",a1,a2); J(setVariable)(e,c,(jstring)a1,(jstring)a2); puts("ok"); }
      else if (!strcmp(cmd,"load")) { sscanf(line,"%*s %s %s %ld",a1,a2,&x); printf("%d %s\n", J(loadGame)(e,c,(jstring)a1,(jstring)a2,(jint)x), CdromId); }
      else if (!strcmp(cmd,"run")) { sscanf(line,"%*s %ld",&x); for(long i=0;i<x;i++){ J(runFrame)(e,c); J(readAudio)(e,c,(jshortArray)&aa);} puts("ok"); }
      else if (!strcmp(cmd,"btn")) { sscanf(line,"%*s %lx",&x); J(setButtons)(e,c,0,(jint)x); puts("ok"); }
      else if (!strcmp(cmd,"axes")) { sscanf(line,"%*s %ld %ld %ld %ld",&x,&y,&z,&w); J(setAxes)(e,c,0,x,y,z,w); puts("ok"); }
      else if (!strcmp(cmd,"analog")) { sscanf(line,"%*s %ld",&x); J(setAnalogMode)(e,c,(jboolean)x); puts("ok"); }
      else if (!strcmp(cmd,"stickdpad")) { sscanf(line,"%*s %ld",&x); J(setStickDpad)(e,c,(jboolean)x,13000); puts("ok"); }
      else if (!strcmp(cmd,"cheat")) { char *p=strchr(line,' '); p=p?p+1:line; long en=0; int i=0; sscanf(p,"%d %ld %[^\n]",&i,&en,a1); J(setCheat)(e,c,i,(jboolean)en,(jstring)a1); puts("ok"); }
      else if (!strcmp(cmd,"xga")) { int on=0,op=0; char hx[256]=""; sscanf(line,"%*s %d %d %255s",&on,&op,hx); static Arr pa; static unsigned char pb[0xC00]; Arr *pp=NULL;
         if (hx[0]) { FILE*f=fopen(hx,"rb"); pa.len=f?fread(pb,1,sizeof pb,f):0; if(f)fclose(f); pa.data=pb; pp=&pa; }
         J(setAnalogMod)(e,c,(jbyteArray)pp,(jboolean)on,op); printf("%d\n",J(analogModState)(e,c)); }
      else if (!strcmp(cmd,"diag")) { const char *r=(const char*)J(diagnostics)(e,c); fputs(r,stdout); puts("<<end>>"); }
      else if (!strcmp(cmd,"xgastate")) { printf("%d\n",J(analogModState)(e,c)); }
      else if (!strcmp(cmd,"clearcheats")) { J(clearCheats)(e,c); puts("ok"); }
      else if (!strcmp(cmd,"read")) { sscanf(line,"%*s %lx %ld",&x,&y); Arr *r=(Arr*)J(readRam)(e,c,(jint)x,(jint)y); if(!r){puts("-1");continue;} for(int i=0;i<y;i++) printf("%02x",((unsigned char*)r->data)[i]); puts(""); }
      else if (!strcmp(cmd,"save")) { sscanf(line,"%*s %s",a1); printf("%d\n",J(saveState)(e,c,(jstring)a1)); }
      else if (!strcmp(cmd,"loadstate")) { sscanf(line,"%*s %s",a1); printf("%d\n",J(loadState)(e,c,(jstring)a1)); }
      else if (!strcmp(cmd,"shot")) { sscanf(line,"%*s %s",a1); jint wh=J(copyFrame)(e,c,(jobject)&b,-1,(jintArray)&seq); int W=wh>>16,H=wh&0xffff; FILE*f=fopen(a1,"wb"); fprintf(f,"P6 %d %d 255\n",W,H);
           for(int i=0;i<W*H;i++){unsigned p=fb[i]; unsigned char px[3]={(p>>11)<<3,((p>>5)&63)<<2,(p&31)<<3}; fwrite(px,1,3,f);} fclose(f); printf("%d %d\n",W,H); }
      else if (!strcmp(cmd,"cardstatus")) { printf("%d\n", J(cardStatus)(e,c)); }
      /* discs, as the app's launcher (appendDisc) and pause menu (setDisc) use them */
      else if (!strcmp(cmd,"appenddisc")) { sscanf(line,"%*s %s",a1); printf("%d\n", J(appendDisc)(e,c,(jstring)a1)); }
      else if (!strcmp(cmd,"setdisc")) { sscanf(line,"%*s %ld",&x); printf("%d\n", J(setDisc)(e,c,(jint)x)); }
      else if (!strcmp(cmd,"discs")) { printf("%d %d\n", J(discIndex)(e,c), J(discCount)(e,c)); }
      else if (!strcmp(cmd,"reset")) { J(reset)(e,c); puts("ok"); }
      else if (!strcmp(cmd,"gameid")) { puts(CdromId); }
      /* developer tools, as Link's DEV section uses them; dumpram writes the 2 MB of main RAM for hint_sweep.py */
      else if (!strcmp(cmd,"devstory")) { sscanf(line,"%*s %ld",&x); J(devStory)(e,c,(jint)x); puts("ok"); }
      else if (!strcmp(cmd,"devwarp")) { sscanf(line,"%*s %ld %ld",&x,&y); J(devWarp)(e,c,(jint)x,(jint)y); puts("ok"); }
      else if (!strcmp(cmd,"devstate")) { printf("%d\n",J(devWarpState)(e,c)); }
      else if (!strcmp(cmd,"devcan")) { uint8_t *r=retro_get_memory_data(RETRO_MEMORY_SYSTEM_RAM); printf("%d\n",dev_can_warp(r)); }
      else if (!strcmp(cmd,"dumpram")) { sscanf(line,"%*s %s",a1); uint8_t *r=retro_get_memory_data(RETRO_MEMORY_SYSTEM_RAM); FILE*f=fopen(a1,"wb"); fwrite(r,1,0x200000,f); fclose(f); puts("ok"); }
      /* stateBytes, as the safety save uses it: written to a file here so it can be loaded back with loadstate */
      else if (!strcmp(cmd,"statebytes")) { sscanf(line,"%*s %s",a1); Arr *r=(Arr*)J(stateBytes)(e,c); if(!r){puts("-1");continue;} FILE*f=fopen(a1,"wb"); fwrite(r->data,1,r->len,f); fclose(f); printf("%d\n",r->len); }
      else if (!strcmp(cmd,"quit")) { J(unload)(e,c); puts("bye"); break; }
      else puts("?");
   }
   return 0;
}
