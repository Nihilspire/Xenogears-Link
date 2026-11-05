#include <stdio.h>
#include <stdlib.h>
#include <libchdr/chd.h>
int main(int c,char**v){ chd_file*f; if(chd_open(v[1],CHD_OPEN_READ,NULL,&f))return 1;
 const chd_header*h=chd_get_header(f); unsigned fpb=h->hunkbytes/2448; unsigned char*b=malloc(h->hunkbytes);
 FILE*o=fopen(v[2],"wb"); unsigned long long total=atoll(v[3]),n=0;
 for(unsigned hn=0;hn<h->totalhunks&&n<total;hn++){ if(chd_read(f,hn,b))return 2; for(unsigned k=0;k<fpb&&n<total;k++,n++) fwrite(b+k*2448,1,2352,o);} fclose(o); return 0;}
