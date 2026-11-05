// dump the CHD as a 2048-byte-per-sector user-data iso (mode2 form1 assumed)
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <libchdr/chd.h>
int main(int c,char**v){
  chd_file*f; if(chd_open(v[1],CHD_OPEN_READ,NULL,&f)!=CHDERR_NONE){puts("open fail");return 1;}
  const chd_header*h=chd_get_header(f);
  unsigned fpb=h->hunkbytes/2448; unsigned char*buf=malloc(h->hunkbytes);
  FILE*o=fopen(v[2],"wb"); unsigned maxs=atoi(v[3]);
  for(unsigned hn=0;hn<h->totalhunks;hn++){
    if(chd_read(f,hn,buf)!=CHDERR_NONE){printf("read fail %u\n",hn);break;}
    for(unsigned k=0;k<fpb;k++){unsigned s=hn*fpb+k; if(s>=maxs) goto done;
      fwrite(buf+k*2448+24,1,2048,o);}
  }
done: fclose(o); printf("hunkbytes %u fpb %u\n",h->hunkbytes,fpb); return 0;}
