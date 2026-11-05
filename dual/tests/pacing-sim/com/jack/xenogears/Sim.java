package com.jack.xenogears;
import android.media.AudioTrack;
public class Sim { public static void main(String[] a) throws Exception {
  double hz=Double.parseDouble(a[0]); Emu e=new Emu(); e.displayHz=(float)hz; e.start();
  java.lang.reflect.Field lv=Emu.class.getDeclaredField("lastVsync"); lv.setAccessible(true);
  long vs=(long)(1e9/hz); long minFill=Long.MAX_VALUE,maxFill=0; long frames0=0;
  for(int i=0;i<(int)(hz*600);i++){ Emu.testClockNs=(long)(i*1e9/hz); e.vsync(); AudioTrack.last.advance(vs);
     java.lang.reflect.Field w=Emu.class.getDeclaredField("written"); w.setAccessible(true); long fill=(long)w.get(e)-AudioTrack.last.getPlaybackHeadPosition();
     if(i>hz*5){minFill=Math.min(minFill,fill);maxFill=Math.max(maxFill,fill);} }
  System.out.printf("display %.2f Hz: game frames %d in 600 s (%.3f fps), audio underrun samples %d, dropped %d, buffer fill %d..%d frames (%.0f..%.0f ms)%n",
     hz,e.frameCount,e.frameCount/600.0,AudioTrack.underruns,AudioTrack.drops,minFill,maxFill,minFill*1000/44100.0,maxFill*1000/44100.0);
}}
