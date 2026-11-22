from pathlib import Path

root=Path("source/ChessTitansAndroid")
src=root/"app/src/main/java/com/example/chesstitans/ChessBoardView.kt"
s=src.read_text()
s=s.replace("private data class Move(", "data class Move(").replace("private class Position(", "class Position(").replace("private object Engine {", "object Engine {")
src.write_text(s)

p=root/"app/src/main/java/com/example/chesstitans/render/ChessTitans3DRenderer.kt"
s=p.read_text()
s=s.replace("import android.opengl.Matrix\n", "import android.opengl.Matrix\nimport android.media.SoundPool\nimport android.media.AudioAttributes\nimport com.example.chesstitans.Position\nimport com.example.chesstitans.Move\nimport com.example.chesstitans.Engine\nimport com.example.chesstitans.R\n")
s=s.replace("@Volatile var cameraPitch = 45f", "@Volatile var cameraPitch = 38f").replace("@Volatile var cameraDistance = 80f", "@Volatile var cameraDistance = 58f")
s=s.replace("@Volatile private var pieceMaterial=0", "@Volatile private var pieceMaterial=1")
s=s.replace("fun resetCamera() { cameraYaw=0f; cameraPitch=45f; cameraDistance=80f }", "fun resetCamera() { cameraYaw=0f; cameraPitch=38f; cameraDistance=58f }")
fields="""    private var chess=Position()
    private data class GameSnapshot(val position:Position,val captured:List<BoardPiece>,val repetitions:List<String>)
    private val gameHistory=mutableListOf<GameSnapshot>()
    private val capturedPieces=mutableListOf<BoardPiece>()
    private val repetitionKeys=mutableListOf<String>()
    private var legalMoves=emptyList<Move>()
    @Volatile private var aiThinking=false
    @Volatile private var aiLevel=2
    private var gameOverSoundPlayed=false
    @Volatile private var pendingAiMove:Move?=null
    @Volatile private var aiResultReady=false
    @Volatile private var gameGeneration=0
    @Volatile var statusCallback:((String)->Unit)?=null
    private var soundPool:SoundPool?=null
    private val soundIds=mutableMapOf<String,Int>()
    private var soundReady=false
"""
if "private var chess=Position()" not in s:
    s=s.replace("    private val boardPieces=mutableListOf<BoardPiece>()\n", "    private val boardPieces=mutableListOf<BoardPiece>()\n"+fields,1)
a=s.index("    private fun resetPosition(){")
b=s.index("    private val shaderV=",a)
game="""    private fun resetPosition(){
        gameGeneration++;aiThinking=false;pendingAiMove=null;aiResultReady=false;gameOverSoundPlayed=false
        chess=Position();gameHistory.clear();capturedPieces.clear();repetitionKeys.clear();repetitionKeys.add(chess.repetitionKey())
        boardPieces.clear();selectedFile=-1;selectedRank=-1;legalMoves=emptyList();animatedPiece=null
        lastFromFile=-1;lastFromRank=-1;lastToFile=-1;lastToRank=-1
        syncPieces();updateStatus()
    }
    private fun syncPieces(){
        boardPieces.clear()
        for(sq in 0..63){val c=chess.b[sq];if(c=='.')continue
            val type=when(c.uppercaseChar()){'K'->"KING";'Q'->"QUEEN";'B'->"BISHOP";'N'->"KNIGHT";'R'->"ROOK";else->"PAWN"}
            boardPieces.add(BoardPiece(type,c.isUpperCase(),sq%8,7-sq/8))
        }
    }
    private fun squareIndex(file:Int,rank:Int)=(7-rank)*8+file
    private fun selectSquare(file:Int,rank:Int){selectedFile=file;selectedRank=rank;legalMoves=chess.legal().filter{it.from==squareIndex(file,rank)}}
    fun screenTap(x:Float,y:Float){
        if(viewportWidth<=0||viewportHeight<=0||aiThinking||!chess.white||isGameOver())return
        Matrix.multiplyMM(vp,0,projection,0,view,0);if(!Matrix.invertM(invVp,0,vp,0))return
        val nx=2f*x/viewportWidth-1f;val ny=1f-2f*y/viewportHeight
        val near=FloatArray(4);val far=FloatArray(4)
        Matrix.multiplyMV(near,0,invVp,0,floatArrayOf(nx,ny,-1f,1f),0)
        Matrix.multiplyMV(far,0,invVp,0,floatArrayOf(nx,ny,1f,1f),0)
        if(abs(near[3])<1e-6f||abs(far[3])<1e-6f)return
        for(i in 0..2){near[i]/=near[3];far[i]/=far[3]}
        val dy=far[1]-near[1];if(abs(dy)<1e-6f)return
        val t=(0.08f-near[1])/dy;if(t<0f)return
        val wx=near[0]+(far[0]-near[0])*t;val wz=near[2]+(far[2]-near[2])*t
        if(wx !in -20f..20f||wz !in -20f..20f)return
        val file=((wx+20f)/5f).toInt().coerceIn(0,7);val rank=((20f-wz)/5f).toInt().coerceIn(0,7)
        val sq=squareIndex(file,rank);val at=chess.b[sq]
        if(selectedFile<0){if(at!='.'&&at.isUpperCase())selectSquare(file,rank)}
        else if(file==selectedFile&&rank==selectedRank){selectedFile=-1;selectedRank=-1;legalMoves=emptyList()}
        else if(at!='.'&&at.isUpperCase())selectSquare(file,rank)
        else {val move=legalMoves.firstOrNull{it.to==sq};if(move!=null)applyMove(move)else playSound("illegal")}
    }
    private fun applyMove(move:Move){
        if(aiThinking&&chess.white)return
        val fromFile=move.from%8;val fromRank=7-move.from/8;val toFile=move.to%8;val toRank=7-move.to/8
        val captured=chess.b[move.to]!='.'||move.ep
        val captureSquare=if(move.ep)move.to+(if(chess.white)8 else -8)else move.to;val capturedChar=chess.b[captureSquare];gameHistory.add(GameSnapshot(chess.copy(),capturedPieces.toList(),repetitionKeys.toList()));if(capturedChar!='.'){val capturedType=when(capturedChar.uppercaseChar()){'K'->"KING";'Q'->"QUEEN";'B'->"BISHOP";'N'->"KNIGHT";'R'->"ROOK";else->"PAWN"};capturedPieces.add(BoardPiece(capturedType,capturedChar.isUpperCase(),-1,-1))};chess.apply(move);repetitionKeys.add(chess.repetitionKey())
        syncPieces();val moved=boardPieces.firstOrNull{it.file==toFile&&it.rank==toRank}
        if(moved!=null){animFromFile=fromFile;animFromRank=fromRank;lastFromFile=fromFile;lastFromRank=fromRank;lastToFile=toFile;lastToRank=toRank;animatedPiece=moved;animStartNanos=System.nanoTime()}
        selectedFile=-1;selectedRank=-1;legalMoves=emptyList()
        playSound(if(captured)"capture" else "move");if(chess.inCheck(chess.white))playSound("check")
        updateStatus();if(!chess.white&&!isGameOver())startAI()
    }
    private fun startAI(){
        if(aiThinking||chess.white||isGameOver())return
        aiThinking=true;updateStatus();val generation=gameGeneration;val snapshot=chess.copy();val moves=snapshot.legal()
        Thread{val choice=if(moves.isNotEmpty())Engine.choose(snapshot,moves,aiLevel)else null
            if(generation==gameGeneration){pendingAiMove=choice;aiResultReady=true}
        }.start()
    }
    private fun processAIResult(){
        if(!aiResultReady)return
        aiResultReady=false;val move=pendingAiMove;pendingAiMove=null
        if(aiThinking&&move!=null&&!chess.white&&chess.legal().any{it==move}){aiThinking=false;applyMove(move)}else aiThinking=false
        updateStatus()
    }
    fun undo(){
        gameGeneration++;aiThinking=false;pendingAiMove=null;aiResultReady=false
        if(gameHistory.isNotEmpty()){
            var snapshot=gameHistory.removeAt(gameHistory.lastIndex)
            if(!snapshot.position.white&&gameHistory.isNotEmpty())snapshot=gameHistory.removeAt(gameHistory.lastIndex)
            chess=snapshot.position.copy();capturedPieces.clear();capturedPieces.addAll(snapshot.captured)
            gameOverSoundPlayed=false;repetitionKeys.clear();repetitionKeys.addAll(snapshot.repetitions);selectedFile=-1;selectedRank=-1;legalMoves=emptyList();animatedPiece=null;syncPieces();updateStatus()
        }
    }
    fun cycleDifficulty():String{aiLevel=aiLevel%3+1;return "AI "+aiLevel}
    fun newGame(){resetPosition();playSound("move")}
    private fun isGameOver():Boolean{
        val lm=chess.legal()
        return lm.isEmpty()||chess.half>=100||repetitionKeys.count{it==chess.repetitionKey()}>=3||chess.insufficientMaterial()
    }
    private fun updateStatus(){
        val lm=chess.legal()
        if(lm.isEmpty()&&chess.inCheck(chess.white)&&!gameOverSoundPlayed){gameOverSoundPlayed=true;playSound(if(chess.white)"lose" else "win")}
        val msg=when{
            lm.isEmpty()&&chess.inCheck(chess.white)->if(chess.white)"Skakmat — Hitam menang" else "Skakmat — Putih menang"
            lm.isEmpty()->"Remis — stalemate"
            chess.half>=100->"Remis — 50 langkah"
            repetitionKeys.count{it==chess.repetitionKey()}>=3->"Remis — posisi berulang"
            chess.insufficientMaterial()->"Remis — materi tidak cukup"
            chess.inCheck(chess.white)->if(chess.white)"Putih sedang skak" else "Hitam sedang skak"
            aiThinking->"Hitam berpikir…"
            chess.white->"Giliran Putih"
            else->"Giliran Hitam"
        }
        statusCallback?.invoke(msg)
    }
    private fun initSounds(){
        if(soundPool!=null)return
        val attrs=AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_GAME).setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION).build()
        soundPool=SoundPool.Builder().setMaxStreams(4).setAudioAttributes(attrs).build()
        soundIds["move1"]=soundPool!!.load(context,R.raw.move1,1);soundIds["move2"]=soundPool!!.load(context,R.raw.move2,1);soundIds["move3"]=soundPool!!.load(context,R.raw.move3,1);soundIds["move4"]=soundPool!!.load(context,R.raw.move4,1);soundIds["move5"]=soundPool!!.load(context,R.raw.move5,1);soundIds["move6"]=soundPool!!.load(context,R.raw.move6,1);soundIds["capture"]=soundPool!!.load(context,R.raw.capture,1);soundIds["check"]=soundPool!!.load(context,R.raw.check,1);soundIds["win"]=soundPool!!.load(context,R.raw.win,1);soundIds["lose"]=soundPool!!.load(context,R.raw.lose,1);soundIds["illegal"]=soundPool!!.load(context,R.raw.illegal,1)
        soundReady=true
    }
    private fun playSound(key:String){if(!soundReady)return;val id=if(key=="move")soundIds["move${(1..6).random()}"] else soundIds[key];if(id!=null)soundPool?.play(id,0.82f,0.82f,1,0,1f)}
    fun release(){soundPool?.release();soundPool=null;soundReady=false}
"""
s=s[:a]+game+s[b:]
s=s.replace("private val animDurationNanos=320_000_000L", "private var animDurationNanos=320_000_000L")
s=s.replace("private var animFromFile=0; private var animFromRank=0; private var animStartNanos=0L", "private var animFromFile=0; private var animFromRank=0; private var animStartNanos=0L; private var animFromWorldX=0f; private var animFromWorldZ=0f; private var animPath=emptyList<FloatArray>(); private val animationCache=mutableMapOf<String,List<FloatArray>>()")
s=s.replace("if(moved!=null){animFromFile=fromFile;animFromRank=fromRank;lastFromFile=fromFile;lastFromRank=fromRank;lastToFile=toFile;lastToRank=toRank;animatedPiece=moved;animStartNanos=System.nanoTime()}", "if(moved!=null){startMoveAnimation(fromFile,fromRank,toFile,toRank);lastFromFile=fromFile;lastFromRank=fromRank;lastToFile=toFile;lastToRank=toRank;animatedPiece=moved}")
helpers="""    private fun animationData(name:String):List<FloatArray> = animationCache.getOrPut(name){
        try{val lines=context.assets.open("original_resources/MEDIA/ANIMATIONS/$name.CAN").bufferedReader().use{it.readLines()};val n=lines.first().trim().toInt();val start=1+n;lines.subList(start,start+n).map{line->line.split(",").map{it.trim().toFloat()}.toFloatArray()}}catch(_:Exception){emptyList()}
    }
    private fun startMoveAnimation(fromFile:Int,fromRank:Int,toFile:Int,toRank:Int){
        animFromWorldX=-17.5f+fromFile*5f;animFromWorldZ=17.5f-fromRank*5f
        val dx=toFile-fromFile;val dz=fromRank-toRank;val ax=abs(dx);val az=abs(dz)
        fun word(n:Int)=when(n){1->"ONE";2->"TWO";3->"THREE";4->"FOUR";5->"FIVE";6->"SIX";7->"SEVEN";else->"ZERO"}
        val name=when{ax==az&&ax>0->word(ax)+"BY"+word(az);az==0&&ax>0->word(ax)+"BYZERO";ax==0&&az>0->word(az)+"BYZERO";maxOf(ax,az)==2&&minOf(ax,az)==1->"TWOBYONE";else->null}
        val raw=name?.let{animationData(it)}?:emptyList()
        if(raw.isNotEmpty()){
            val end=raw.last();val targetX=dx*5f;val targetZ=dz*5f
            animPath=raw.map{f->floatArrayOf(if(abs(end[0])>0.001f)f[0]/end[0]*targetX else 0f,f[1],if(abs(end[2])>0.001f)f[2]/end[2]*targetZ else if(abs(end[0])>0.001f)f[0]/end[0]*targetZ else 0f)}
        }else{
            animPath=(0..20).map{i->val t=i/20f;val e=t*t*(3f-2f*t);floatArrayOf(dx*5f*e,0.82f*4f*t*(1f-t),dz*5f*e)}
        }
        animDurationNanos=(animPath.size*24_000_000L).coerceAtLeast(240_000_000L);animStartNanos=System.nanoTime()
    }
"""
s=s.replace("    private val shaderV=", helpers+"    private val shaderV=",1)

# exact render tweaks and safeguards
s=s.replace('listOf("KING","QUEEN","BISHOP","KNIGHT","ROOK","PAWN").forEach { pieces[it]=ObjMesh.load(context,"meshes/high/$it.obj") }; resetPosition()', 'listOf("KING","QUEEN","BISHOP","KNIGHT","ROOK","PAWN").forEach { pieces[it]=ObjMesh.load(context,"meshes/high/$it.obj") }; initSounds(); resetPosition()')
s=s.replace('Matrix.perspectiveM(projection,0,36f,aspect,1f,220f)', 'Matrix.perspectiveM(projection,0,36f,aspect,1f,220f)')
s=s.replace('    override fun onDrawFrame(gl: GL10?) {\\n        updateCamera()', '    override fun onDrawFrame(gl: GL10?) {\\n        processAIResult()\\n        updateCamera()')
s=s.replace('draw(pieces[p.type]!!,x,0.06f+lift,z,0.42f,c[0],c[1],c[2],0,tex,pieceMaterial)', 'draw(pieces[p.type]!!,x,0.06f+lift,z,0.42f,c[0],c[1],c[2],0,tex,pieceMaterial,if(p.white)0f else 180f)')
s=s.replace('private fun draw(mesh:ObjMesh,x:Float,y:Float,z:Float,s:Float,r:Float,g:Float,b:Float,checker:Int,texture:Int,material:Int=0){', 'private fun draw(mesh:ObjMesh,x:Float,y:Float,z:Float,s:Float,r:Float,g:Float,b:Float,checker:Int,texture:Int,material:Int=0,rotationY:Float=0f){')
s=s.replace('Matrix.scaleM(model,0,s,s,s)\\n        Matrix.multiplyMM(mvp', 'Matrix.scaleM(model,0,s,s,s)\\n        if(rotationY!=0f)Matrix.rotateM(model,0,rotationY,0f,1f,0f)\\n        Matrix.multiplyMM(mvp')
s=s.replace('drawSquareHighlight(selectedFile,selectedRank,0.95f,0.80f,0.22f,0.34f)\n        for(p in boardPieces) place(p)', 'drawSquareHighlight(selectedFile,selectedRank,0.95f,0.80f,0.22f,0.34f)\n        for(move in legalMoves){val f=move.to%8;val r=7-move.to/8;val capture=chess.b[move.to]!=\'.\'||move.ep;drawSquareHighlight(f,r,if(capture)0.86f else 0.18f,if(capture)0.24f else 0.62f,if(capture)0.18f else 0.98f,0.30f)}\n        for(p in boardPieces) place(p)')
a=s.index("    private fun place(p:BoardPiece){")
b=s.index("    private fun drawSquareHighlight",a)
place="""    private fun place(p:BoardPiece){
        var x=-17.5f+p.file*5f;var z=17.5f-p.rank*5f;var lift=0f
        if(p===animatedPiece&&animPath.isNotEmpty()){
            val progress=((System.nanoTime()-animStartNanos).toFloat()/animDurationNanos).coerceIn(0f,1f)
            val samplePos=progress*(animPath.lastIndex);val lo=samplePos.toInt().coerceIn(0,animPath.lastIndex);val hi=(lo+1).coerceIn(0,animPath.lastIndex);val t=samplePos-lo
            val sample=FloatArray(3){i->animPath[lo][i]+(animPath[hi][i]-animPath[lo][i])*t}
            x=animFromWorldX+sample[0];z=animFromWorldZ+sample[2];lift=sample[1]
            if(progress>=1f)animatedPiece=null
        }
        drawShadow(x,z,0.065f)
        val c=if(pieceMaterial==1){if(p.white)floatArrayOf(0.88f,0.90f,0.93f)else floatArrayOf(0.16f,0.18f,0.21f)}else if(p.white)floatArrayOf(0.94f,0.91f,0.83f)else floatArrayOf(0.42f,0.38f,0.33f)
        val tex=if(pieceMaterial==0)if(p.white)whitePieceTex else blackPieceTex else 0
        draw(pieces[p.type]!!,x,0.06f+lift,z,0.42f,c[0],c[1],c[2],0,tex,pieceMaterial,if(p.white)0f else 180f)
    }
"""
s=s[:a]+place+s[b:]
s=s.replace("        for(p in boardPieces) place(p)", "        for(p in boardPieces) place(p)\n        drawCapturedPieces()")
captured="""    private fun drawCapturedPieces(){
        val whiteCaptured=capturedPieces.filter{it.white};val blackCaptured=capturedPieces.filter{!it.white}
        whiteCaptured.forEachIndexed{i,p->placeCaptured(p,i,true)}
        blackCaptured.forEachIndexed{i,p->placeCaptured(p,i,false)}
    }
    private fun placeCaptured(p:BoardPiece,index:Int,whiteSide:Boolean){
        val col=index/8;val row=index%8;val x=if(whiteSide)22.8f+col*2.7f else -22.8f-col*2.7f;val z=17.5f-row*4.2f
        drawShadow(x,z,0.065f)
        val c=if(pieceMaterial==1){if(p.white)floatArrayOf(0.88f,0.90f,0.93f)else floatArrayOf(0.16f,0.18f,0.21f)}else if(p.white)floatArrayOf(0.94f,0.91f,0.83f)else floatArrayOf(0.42f,0.38f,0.33f)
        val tex=if(pieceMaterial==0)if(p.white)whitePieceTex else blackPieceTex else 0
        draw(pieces[p.type]!!,x,0.06f,z,0.28f,c[0],c[1],c[2],0,tex,pieceMaterial,if(p.white)0f else 180f)
    }
"""
s=s.replace("    private fun drawSquareHighlight", captured+"    private fun drawSquareHighlight",1)
s=s.replace("if(capture)0.86f else 0.30f,if(capture)0.24f else 0.72f,if(capture)0.18f else 0.35f,0.22f", "if(capture)0.86f else 0.18f,if(capture)0.24f else 0.62f,if(capture)0.18f else 0.98f,0.30f")
p.write_text(s)
raw=root/"app/src/main/res/raw";raw.mkdir(parents=True,exist_ok=True)
soundRoot=root/"app/src/main/assets/original_resources/MEDIA/SOUND"
for srcName,dstName in [("MOVEPIECE1.WAV","move1.wav"),("MOVEPIECE2.WAV","move2.wav"),("MOVEPIECE3.WAV","move3.wav"),("MOVEPIECE4.WAV","move4.wav"),("MOVEPIECE5.WAV","move5.wav"),("MOVEPIECE6.WAV","move6.wav"),("CHESS_PIECETAKEN.WAV","capture.wav"),("CHECK.WAV","check.wav"),("CHECKMATEWIN.WAV","win.wav"),("CHECKMATELOSE.WAV","lose.wav"),("ILLEGALMOVE.WAV","illegal.wav")]:
    (raw/dstName).write_bytes((soundRoot/srcName).read_bytes())

activity=root/"app/src/main/java/com/example/chesstitans/ChessTitans3DPreviewActivity.kt"
activity.write_text("""package com.example.chesstitans

import android.app.Activity
import android.opengl.GLSurfaceView
import android.os.Bundle
import android.view.MotionEvent
import android.view.View
import android.view.WindowManager
import android.widget.Button
import android.widget.FrameLayout
import android.widget.LinearLayout
import android.widget.TextView
import android.graphics.Color
import com.example.chesstitans.render.ChessTitans3DRenderer

/** Main Android port using the extracted high-detail meshes and real chess rules. */
class ChessTitans3DPreviewActivity:Activity(){
    private lateinit var gl:GLSurfaceView
    private lateinit var renderer:ChessTitans3DRenderer
    private lateinit var status:TextView
    override fun onCreate(savedInstanceState:Bundle?){
        super.onCreate(savedInstanceState)
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        @Suppress("DEPRECATION")
        window.decorView.systemUiVisibility=(View.SYSTEM_UI_FLAG_FULLSCREEN or View.SYSTEM_UI_FLAG_HIDE_NAVIGATION or View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY or View.SYSTEM_UI_FLAG_LAYOUT_STABLE or View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION or View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN)
        gl=GLSurfaceView(this).apply{setEGLContextClientVersion(2)}
        renderer=ChessTitans3DRenderer(this);renderer.statusCallback={message->runOnUiThread{status.text=message}}
        gl.setRenderer(renderer);gl.renderMode=GLSurfaceView.RENDERMODE_CONTINUOUSLY
        gl.setOnTouchListener{_,event->if(event.action==MotionEvent.ACTION_UP)gl.queueEvent{renderer.screenTap(event.x,event.y)};true}
        val root=FrameLayout(this);root.addView(gl,FrameLayout.LayoutParams(-1,-1))
        val top=LinearLayout(this).apply{orientation=LinearLayout.HORIZONTAL;setPadding(dp(8),dp(4),dp(8),dp(4));setBackgroundColor(0x770d1721.toInt())}
        fun button(label:String,action:()->Unit)=Button(this).apply{text=label;setTextColor(Color.WHITE);setOnClickListener{action()}}
        top.addView(button("Undo"){gl.queueEvent{renderer.undo()}},LinearLayout.LayoutParams(0,dp(44),1f))
        top.addView(button("Baru"){gl.queueEvent{renderer.newGame()}},LinearLayout.LayoutParams(0,dp(44),1f))
        lateinit var boardButton:Button
        boardButton=button("Marmer"){gl.queueEvent{renderer.cycleTheme();runOnUiThread{boardButton.text=renderer.themeName()}}}
        top.addView(boardButton,LinearLayout.LayoutParams(0,dp(44),1f))
        lateinit var pieceButton:Button
        pieceButton=button("Porcelain"){gl.queueEvent{renderer.cyclePieceMaterial();runOnUiThread{pieceButton.text=renderer.pieceMaterialName()}}}
        top.addView(pieceButton,LinearLayout.LayoutParams(0,dp(44),1f))
        lateinit var levelButton:Button
        levelButton=button("AI 2"){gl.queueEvent{val label=renderer.cycleDifficulty();runOnUiThread{levelButton.text=label}}}
        top.addView(levelButton,LinearLayout.LayoutParams(0,dp(44),1f))
        root.addView(top,FrameLayout.LayoutParams(-1,-2,android.view.Gravity.TOP))
        status=TextView(this).apply{text="Putih jalan";setTextColor(Color.WHITE);textSize=15f;gravity=android.view.Gravity.CENTER;setPadding(dp(10),dp(7),dp(10),dp(7));setBackgroundColor(0x770d1721.toInt())}
        root.addView(status,FrameLayout.LayoutParams(-1,-2,android.view.Gravity.BOTTOM))
        setContentView(root)
    }
    private fun dp(v:Int)=(v*resources.displayMetrics.density).toInt()
    override fun onPause(){super.onPause();if(::gl.isInitialized)gl.onPause()}
    override fun onResume(){super.onResume();if(::gl.isInitialized)gl.onResume()}
    override fun onDestroy(){if(::renderer.isInitialized)renderer.release();super.onDestroy()}
}
""")
(root/"app/src/main/AndroidManifest.xml").write_text("""<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
  <application android:theme="@style/AppTheme" android:label="Chess Titans" android:allowBackup="false" android:supportsRtl="true">
    <activity android:name=".MainActivity" android:screenOrientation="landscape" android:exported="false"/>
    <activity android:name=".ChessTitans3DPreviewActivity" android:screenOrientation="landscape" android:exported="true">
      <intent-filter><action android:name="android.intent.action.MAIN"/><category android:name="android.intent.category.LAUNCHER"/></intent-filter>
    </activity>
  </application>
</manifest>
""")
print("Patched: 3D launcher, legal chess, background AI, sound hooks, fixed camera, themes and original high meshes.")
