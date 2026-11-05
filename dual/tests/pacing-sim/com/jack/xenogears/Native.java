package com.jack.xenogears;
final class Native {
  static double emuTime=0; static long samplesMade=0; static double phase=0; static int pending=0;
  static double fps(){return 59.94;} static double sampleRate(){return 44100;}
  static void runFrame(){ double per=44100/59.94; phase+=per; int n=(int)phase; phase-=n; pending+=n; }
  static int readAudio(short[] o){ int n=Math.min(pending,o.length/2); for(int i=0;i<n;i++){ short v=(short)(10000*Math.sin((samplesMade+i)*2*Math.PI*440/44100)); o[i*2]=v;o[i*2+1]=v;} samplesMade+=n; pending-=n; return n*2; }
  static long memcardHash(){return 1;} static boolean saveMemcard(){return true;} static String pollMessage(int[] s){return null;}
}
