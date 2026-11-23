package com.port.chesstitans

import android.app.Activity
import android.os.Bundle
import android.graphics.*
import android.view.Gravity
import android.view.MotionEvent
import android.view.View
import android.widget.*

class MainActivity : Activity() {
    private val bg=Color.rgb(17,27,38); private val gold=Color.rgb(213,177,104)
    override fun onCreate(savedInstanceState:Bundle?){super.onCreate(savedInstanceState);showMenu()}
    private fun showMenu(){
        val root=LinearLayout(this).apply{orientation=LinearLayout.VERTICAL;gravity=Gravity.CENTER;setBackgroundColor(bg);setPadding(22,16,22,16)}
        root.addView(TextView(this).apply{text="CHESS TITANS";textSize=38f;setTextColor(gold);typeface=Typeface.create("serif",Typeface.BOLD);gravity=Gravity.CENTER},LinearLayout.LayoutParams(-1,-2))
        root.addView(TextView(this).apply{text="NATIVE ANDROID CHESS • PLAYABLE BUILD";textSize=12f;setTextColor(Color.LTGRAY);gravity=Gravity.CENTER;setPadding(0,8,0,28)})
        menuButton(root,"PLAY VS COMPUTER",300,58){showGame(true)}
        menuButton(root,"TWO PLAYER",300,54){showGame(false)}
        menuButton(root,"SETTINGS",300,54){Toast.makeText(this,"Visual settings will be added in a later milestone.",Toast.LENGTH_SHORT).show()}
        menuButton(root,"EXIT",300,54){finish()};setContentView(root)
    }
    private fun menuButton(p:LinearLayout,t:String,w:Int,h:Int,a:()->Unit){val b=Button(this).apply{text=t;textSize=15f;setTextColor(Color.WHITE);setBackgroundColor(Color.rgb(43,61,78))};val lp=LinearLayout.LayoutParams(w,h);lp.setMargins(0,5,0,5);p.addView(b,lp);b.setOnClickListener{a()}}
    private fun showGame(vsAI:Boolean){
        val engine=ChessEngine();val layout=LinearLayout(this).apply{orientation=LinearLayout.VERTICAL;setBackgroundColor(bg)}
        val status=TextView(this).apply{text=engine.status;textSize=15f;setTextColor(gold);gravity=Gravity.CENTER;setPadding(8,10,8,6)}
        layout.addView(status,LinearLayout.LayoutParams(-1,-2))
        val board=BoardView(engine,vsAI){status.text=engine.status;status.invalidate()};layout.addView(board,LinearLayout.LayoutParams(-1,0,1f))
        val row=LinearLayout(this).apply{gravity=Gravity.CENTER}
        menuButton(row,"UNDO",105,46){board.undo();status.text=engine.status}
        menuButton(row,"NEW",105,46){board.reset();status.text=engine.status}
        menuButton(row,"MENU",105,46){showMenu()}
        layout.addView(row,LinearLayout.LayoutParams(-1,-2));setContentView(layout)
    }
    private inner class BoardView(ctx:android.content.Context,val game:ChessEngine,val ai:Boolean,val changed:()->Unit):View(ctx){
        private val p=Paint(Paint.ANTI_ALIAS_FLAG);private var sq=0f;private var l=0f;private var t=0f
        private var selected:Pair<Int,Int>?=null;private var targets=emptyList<ChessEngine.Move>();private val undo=mutableListOf<String>()
        private val unicode=mapOf('K' to "♔",'Q' to "♕",'R' to "♖",'B' to "♗",'N' to "♘",'P' to "♙",'k' to "♚",'q' to "♛",'r' to "♜",'b' to "♝",'n' to "♞",'p' to "♟")
        fun reset(){game.reset();selected=null;targets=emptyList();undo.clear();invalidate();changed()}
        fun undo(){if(game.undo()){if(ai&&game.whiteToMove&&game.undo()){};selected=null;targets=emptyList();invalidate();changed()}else Toast.makeText(this@MainActivity,"Nothing to undo.",Toast.LENGTH_SHORT).show()}
        override fun onDraw(canvas:Canvas){
            super.onDraw(canvas);val margin=28f;sq=minOf((width-2*margin)/8f,(height-2*margin)/8f);l=(width-sq*8)/2;t=(height-sq*8)/2
            val frame=RectF(l-7,t-7,l+sq*8+7,t+sq*8+7);p.shader=LinearGradient(frame.left,frame.top,frame.right,frame.bottom,Color.rgb(107,70,39),Color.rgb(39,24,14),Shader.TileMode.CLAMP);canvas.drawRoundRect(frame,10f,10f,p);p.shader=null
            for(r in 0..7)for(c in 0..7){val x=l+c*sq;val y=t+r*sq;p.color=if((r+c)%2==0)Color.rgb(224,205,164)else Color.rgb(105,75,49);canvas.drawRect(x,y,x+sq,y+sq,p)
                if(selected==Pair(r,c)){p.color=Color.argb(120,240,198,66);canvas.drawRect(x,y,x+sq,y+sq,p)}
                if(targets.any{it.tr==r&&it.tc==c}){p.color=if(game.board[r][c]=='.')Color.argb(120,45,115,75)else Color.argb(130,170,55,40);canvas.drawCircle(x+sq/2,y+sq/2,sq*.13f,p)}
                val ch=game.board[r][c];if(ch!='.'){p.typeface=Typeface.create("serif",Typeface.NORMAL);p.textAlign=Paint.Align.CENTER;p.textSize=sq*.78f;p.color=if(ch.isUpperCase())Color.rgb(250,246,225)else Color.rgb(23,21,19);p.setShadowLayer(2f,1f,2f,Color.BLACK);canvas.drawText(unicode[ch]?:ch.toString(),x+sq/2,y+sq*.78f,p);p.clearShadowLayer()}
            }
            p.color=gold;p.textSize=12f;p.textAlign=Paint.Align.CENTER
            for(i in 0..7){canvas.drawText((8-i).toString(),l-12,t+i*sq+sq/2+4,p);canvas.drawText(('a'.code+i).toChar().toString(),l+i*sq+sq/2,t+sq*8+17,p)}
        }
        override fun onTouchEvent(e:MotionEvent):Boolean{if(e.action!=MotionEvent.ACTION_UP)return true;val c=((e.x-l)/sq).toInt();val r=((e.y-t)/sq).toInt();if(r !in 0..7||c !in 0..7)return true
            val sel=selected
            if(sel==null){if(game.board[r][c]!='.'&&game.board[r][c].isUpperCase()==game.whiteToMove){selected=Pair(r,c);targets=game.legalMoves(r,c)}}
            else {val m=targets.firstOrNull{it.tr==r&&it.tc==c};if(m!=null){game.play(m);selected=null;targets=emptyList();if(ai&&!game.whiteToMove&&game.status!="Checkmate — White wins"&&game.status!="Checkmate — Black wins"&&game.status!="Stalemate"){game.computerMove()};changed()}else if(game.board[r][c]!='.'&&game.board[r][c].isUpperCase()==game.whiteToMove){selected=Pair(r,c);targets=game.legalMoves(r,c)}else{selected=null;targets=emptyList()}}
            invalidate();return true}
    }
}
