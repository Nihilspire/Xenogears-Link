package android.media;
public class AudioTrack {
  public static final int MODE_STREAM=1, WRITE_NON_BLOCKING=1, PLAYSTATE_PLAYING=3, PLAYSTATE_PAUSED=2;
  public static long clockNs; public static int rate; int cap; long written, played; int state=PLAYSTATE_PAUSED;
  public static int underruns, drops; public static long playedTotal;
  public static AudioTrack last;
  public AudioTrack(int st,int r,int ch,int enc,int bytes,int mode){rate=r;cap=bytes/4;last=this;}
  public static int getMinBufferSize(int r,int c,int e){return 3528*4/2*2;}
  public void play(){state=PLAYSTATE_PLAYING;} public void pause(){state=PLAYSTATE_PAUSED;} public void flush(){written=played;} public void release(){}
  public int getPlayState(){return state;}
  /* hardware consumes in 10 ms periods */
  public void advance(long ns){ if(state!=PLAYSTATE_PLAYING) return; long want=(long)(ns*rate/1e9); for(long i=0;i<want;i++){ if(played<written){played++;playedTotal++;} else underruns++; } }
  public int getPlaybackHeadPosition(){return (int)played;}
  public int write(short[] d,int off,int n,int mode){ long room=cap-(written-played); int fr=(int)Math.min(n/2,room); if(fr<n/2) drops+=n/2-fr; written+=fr; return fr*2; }
}
