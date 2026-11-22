from pathlib import Path

root=Path("source/ChessTitansAndroid")
src=root/"app/src/main/java/com/example/chesstitans/ChessBoardView.kt"
s=src.read_text()
s=s.replace("private data class Move(", "data class Move(").replace("private class Position(", "class Position(").replace("private object Engine {", "object Engine {")
src.write_text(s)

p=root/"app/src/main/java/com/example/chesstitans/render/ChessTitans3DRenderer.kt"
s=p.read_text()
s=s.replace("import android.opengl.Matrix\n", "import android.opengl.Matrix\nimport android.media.SoundPool\nimport android.media.AudioAttributes\n")
s=s.replace("@Volatile var cameraPitch = 45f", "@Volatile var cameraPitch = 42f").replace("@Volatile var cameraDistance = 80f", "@Volatile var cameraDistance = 54f")
s=s.replace("fun resetCamera() { cameraYaw=0f; cameraPitch=45f; cameraDistance=80f }", "fun resetCamera() { cameraYaw=0f; cameraPitch=42f; cameraDistance=54f }")
fields="""    private var chess=Position()
    private val gameHistory=mutableListOf<Position>()
    private val repetitionKeys=mutableListOf<String>()
    private var legalMoves=emptyList<Move>()
    @Volatile private var aiThinking=false
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
        gameGeneration++;aiThinking=false;pendingAiMove=null;aiResultReady=false
        chess=Position();gameHistory.clear();repetitionKeys.clear();repetitionKeys.add(chess.repetitionKey())
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
        if(viewportWidth<=0||viewportHeight<=0||aiThinking||!chess.white)return
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
        else {val move=legalMoves.firstOrNull{it.to==sq};if(move!=null)applyMove(move)}
    }
    private fun applyMove(move:Move){
        if(aiThinking&&chess.white)return
        val fromFile=move.from%8;val fromRank=7-move.from/8;val toFile=move.to%8;val toRank=7-move.to/8
        val captured=chess.b[move.to]!='.'||move.ep
        gameHistory.add(chess.copy());chess.apply(move);repetitionKeys.add(chess.repetitionKey())
        syncPieces();val moved=boardPieces.firstOrNull{it.file==toFile&&it.rank==toRank}
        if(moved!=null){animFromFile=fromFile;animFromRank=fromRank;lastFromFile=fromFile;lastFromRank=fromRank;lastToFile=toFile;lastToRank=toRank;animatedPiece=moved;animStartNanos=System.nanoTime()}
        selectedFile=-1;selectedRank=-1;legalMoves=emptyList()
        playSound(if(captured)"capture" else "move");if(chess.inCheck(chess.white))playSound("check")
        updateStatus();if(!chess.white&&!isGameOver())startAI()
    }
    private fun startAI(){
        if(aiThinking||chess.white||isGameOver())return
        aiThinking=true;updateStatus();val generation=gameGeneration;val snapshot=chess.copy();val moves=snapshot.legal()
        Thread{val choice=if(moves.isNotEmpty())Engine.choose(snapshot,moves,2)else null
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
            chess=gameHistory.removeAt(gameHistory.lastIndex)
            if(!chess.white&&gameHistory.isNotEmpty())chess=gameHistory.removeAt(gameHistory.lastIndex)
            repetitionKeys.clear();repetitionKeys.add(chess.repetitionKey());selectedFile=-1;selectedRank=-1;legalMoves=emptyList();animatedPiece=null;syncPieces();updateStatus()
        }
    }
    fun newGame(){resetPosition();playSound("move")}
    private fun isGameOver():Boolean{
        val lm=chess.legal()
        return lm.isEmpty()||chess.half>=100||repetitionKeys.count{it==chess.repetitionKey()}>=3||chess.insufficientMaterial()
    }
    private fun updateStatus(){
        val lm=chess.legal()
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
        soundIds["move1"]=soundPool!!.load(context,R.raw.move1,1);soundIds["move2"]=soundPool!!.load(context,R.raw.move2,1);soundIds["move3"]=soundPool!!.load(context,R.raw.move3,1);soundIds["move4"]=soundPool!!.load(context,R.raw.move4,1);soundIds["move5"]=soundPool!!.load(context,R.raw.move5,1);soundIds["move6"]=soundPool!!.load(context,R.raw.move6,1);soundIds["capture"]=soundPool!!.load(context,R.raw.capture,1);soundIds["check"]=soundPool!!.load(context,R.raw.check,1)
        soundReady=true
    }
    private fun playSound(key:String){if(!soundReady)return;val id=if(key=="move")soundIds["move${(1..6).random()}"] else soundIds[key];if(id!=null)soundPool?.play(id,0.82f,0.82f,1,0,1f)}
    fun release(){soundPool?.release();soundPool=null;soundReady=false}
"""
s=s[:a]+game+s[b:]
# exact render tweaks and safeguards
s=s.replace('listOf("KING","QUEEN","BISHOP","KNIGHT","ROOK","PAWN").forEach { pieces[it]=ObjMesh.load(context,"meshes/high/$it.obj") }; resetPosition()', 'listOf("KING","QUEEN","BISHOP","KNIGHT","ROOK","PAWN").forEach { pieces[it]=ObjMesh.load(context,"meshes/high/$it.obj") }; initSounds(); resetPosition()')
s=s.replace('Matrix.perspectiveM(projection,0,36f,aspect,1f,220f)', 'Matrix.perspectiveM(projection,0,34f,aspect,1f,220f)')
s=s.replace('    override fun onDrawFrame(gl: GL10?) {\\n        updateCamera()', '    override fun onDrawFrame(gl: GL10?) {\\n        processAIResult()\\n        updateCamera()')
s=s.replace('draw(pieces[p.type]!!,x,0.06f+lift,z,0.42f,c[0],c[1],c[2],0,tex,pieceMaterial)', 'draw(pieces[p.type]!!,x,0.06f+lift,z,0.42f,c[0],c[1],c[2],0,tex,pieceMaterial,if(p.white)0f else 180f)')
s=s.replace('private fun draw(mesh:ObjMesh,x:Float,y:Float,z:Float,s:Float,r:Float,g:Float,b:Float,checker:Int,texture:Int,material:Int=0){', 'private fun draw(mesh:ObjMesh,x:Float,y:Float,z:Float,s:Float,r:Float,g:Float,b:Float,checker:Int,texture:Int,material:Int=0,rotationY:Float=0f){')
s=s.replace('Matrix.scaleM(model,0,s,s,s)\\n        Matrix.multiplyMM(mvp', 'Matrix.scaleM(model,0,s,s,s)\\n        if(rotationY!=0f)Matrix.rotateM(model,0,rotationY,0f,1f,0f)\\n        Matrix.multiplyMM(mvp')
p.write_text(s)

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
        val top=LinearLayout(this).apply{orientation=LinearLayout.HORIZONTAL;setPadding(8,4,8,4);setBackgroundColor(0x770d1721.toInt())}
        fun button(label:String,action:()->Unit)=Button(this).apply{text=label;setTextColor(Color.WHITE);setOnClickListener(action)}
        top.addView(button("Undo"){gl.queueEvent{renderer.undo()}},LinearLayout.LayoutParams(0,48,1f))
        top.addView(button("Baru"){gl.queueEvent{renderer.newGame()}},LinearLayout.LayoutParams(0,48,1f))
        top.addView(button("Papan"){gl.queueEvent{renderer.cycleTheme()}},LinearLayout.LayoutParams(0,48,1f))
        top.addView(button("Bidak"){gl.queueEvent{renderer.cyclePieceMaterial()}},LinearLayout.LayoutParams(0,48,1f))
        root.addView(top,FrameLayout.LayoutParams(-1,-2,android.view.Gravity.TOP))
        status=TextView(this).apply{text="Putih jalan";setTextColor(Color.WHITE);textSize=15f;gravity=android.view.Gravity.CENTER;setPadding(10,7,10,7);setBackgroundColor(0x770d1721.toInt())}
        root.addView(status,FrameLayout.LayoutParams(-1,-2,android.view.Gravity.BOTTOM))
        setContentView(root)
    }
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
