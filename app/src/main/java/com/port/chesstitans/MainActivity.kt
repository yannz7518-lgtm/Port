package com.port.chesstitans

import android.app.Activity
import android.os.Bundle
import android.graphics.*
import android.view.Gravity
import android.view.MotionEvent
import android.view.View
import android.widget.*

class MainActivity : Activity() {
    private val bg = Color.rgb(17, 27, 38)
    private val gold = Color.rgb(213, 177, 104)
    override fun onCreate(savedInstanceState: Bundle?) { super.onCreate(savedInstanceState); showMenu() }

    private fun showMenu() {
        val root = LinearLayout(this).apply { orientation=LinearLayout.VERTICAL; gravity=Gravity.CENTER; setBackgroundColor(bg); setPadding(24,18,24,18) }
        val title = TextView(this).apply { text="CHESS TITANS"; textSize=36f; setTextColor(gold); typeface=Typeface.create("serif",Typeface.BOLD); gravity=Gravity.CENTER }
        root.addView(title, LinearLayout.LayoutParams(-1,-2))
        val sub = TextView(this).apply { text="ANDROID PORT • EARLY PLAYABLE BOARD"; textSize=12f; setTextColor(Color.LTGRAY); gravity=Gravity.CENTER; setPadding(0,8,0,24) }
        root.addView(sub)
        button(root,"PLAY",300,58) { showBoard() }
        button(root,"DIFFICULTY",300,52) { Toast.makeText(this,"AI difficulty is not implemented in this prototype.",Toast.LENGTH_SHORT).show() }
        button(root,"SETTINGS",300,52) { Toast.makeText(this,"Settings are planned for later builds.",Toast.LENGTH_SHORT).show() }
        button(root,"EXIT",300,52) { finish() }
        setContentView(root)
    }
    private fun button(parent: LinearLayout, label:String, width:Int, height:Int, action:()->Unit) {
        val b=Button(this).apply { text=label; textSize=16f; setTextColor(Color.WHITE); setBackgroundColor(Color.rgb(43,61,78)); isAllCaps=true }
        val lp=LinearLayout.LayoutParams(width,height); lp.setMargins(0,6,0,6); parent.addView(b,lp); b.setOnClickListener { action() }
    }
    private fun showBoard() {
        val layout=LinearLayout(this).apply { orientation=LinearLayout.VERTICAL; setBackgroundColor(bg) }
        val header=TextView(this).apply { text="CHESS TITANS  •  BOARD PROTOTYPE"; textSize=17f; setTextColor(gold); gravity=Gravity.CENTER; setPadding(8,12,8,8) }
        layout.addView(header,LinearLayout.LayoutParams(-1,-2))
        val board=BoardView(this); layout.addView(board,LinearLayout.LayoutParams(-1,0,1f))
        val footer=LinearLayout(this).apply { gravity=Gravity.CENTER; orientation=LinearLayout.HORIZONTAL }
        button(footer,"RESET",140,48) { board.reset(); board.invalidate() }
        button(footer,"MENU",140,48) { showMenu() }
        layout.addView(footer,LinearLayout.LayoutParams(-1,-2))
        setContentView(layout)
    }

    private inner class BoardView(ctx: android.content.Context): View(ctx) {
        private val paint=Paint(Paint.ANTI_ALIAS_FLAG)
        private val symbols=arrayOf("♜","♞","♝","♛","♚","♝","♞","♜")
        private val whiteSymbols=arrayOf("♖","♘","♗","♕","♔","♗","♘","♖")
        private val pieces=Array(8){Array<String?>(8){null}}
        private val white=Array(8){BooleanArray(8)}
        private var selected: Pair<Int,Int>?=null
        private var square=0f; private var left=0f; private var top=0f
        init { reset() }
        fun reset() {
            for(r in 0..7) for(c in 0..7){ pieces[r][c]=null; white[r][c]=false }
            for(c in 0..7){ pieces[0][c]=symbols[c]; white[0][c]=false; pieces[1][c]="♟"; white[1][c]=false; pieces[6][c]="♙"; white[6][c]=true; pieces[7][c]=whiteSymbols[c]; white[7][c]=true }
            selected=null
        }
        override fun onDraw(canvas:Canvas) {
            super.onDraw(canvas)
            val margin=26f; square=Math.min((width-2*margin)/8f,(height-2*margin)/8f); left=(width-square*8)/2; top=(height-square*8)/2
            val frame=RectF(left-8,top-8,left+square*8+8,top+square*8+8)
            paint.shader=LinearGradient(frame.left,frame.top,frame.right,frame.bottom,Color.rgb(94,62,35),Color.rgb(43,27,16),Shader.TileMode.CLAMP); canvas.drawRoundRect(frame,12f,12f,paint); paint.shader=null
            for(r in 0..7) for(c in 0..7){
                val x=left+c*square; val y=top+r*square
                val light=Color.rgb(224,205,164); val dark=Color.rgb(105,75,49)
                paint.color=if((r+c)%2==0) light else dark
                canvas.drawRect(x,y,x+square,y+square,paint)
                if(selected==Pair(r,c)){paint.color=Color.argb(120,245,210,70);canvas.drawRect(x,y,x+square,y+square,paint)}
                val piece=pieces[r][c]
                if(piece!=null){
                    paint.typeface=Typeface.create("serif",Typeface.NORMAL); paint.textAlign=Paint.Align.CENTER; paint.textSize=square*.78f
                    paint.color=if(white[r][c]) Color.rgb(248,244,225) else Color.rgb(27,24,22)
                    paint.setShadowLayer(2f,1f,2f,Color.BLACK)
                    canvas.drawText(piece,x+square/2,y+square*.78f,paint); paint.clearShadowLayer()
                }
            }
            paint.color=gold; paint.textSize=12f; paint.textAlign=Paint.Align.CENTER
            for(i in 0..7){canvas.drawText((8-i).toString(),left-12,top+i*square+square/2+4,paint);canvas.drawText(('a'.code+i).toChar().toString(),left+i*square+square/2,top+square*8+17,paint)}
        }
        override fun onTouchEvent(event:MotionEvent):Boolean {
            if(event.action!=MotionEvent.ACTION_UP)return true
            val c=((event.x-left)/square).toInt(); val r=((event.y-top)/square).toInt()
            if(r !in 0..7||c !in 0..7)return true
            val from=selected
            if(from==null){if(pieces[r][c]!=null)selected=Pair(r,c)}
            else if(from.first==r&&from.second==c){selected=null}
            else {pieces[r][c]=pieces[from.first][from.second];white[r][c]=white[from.first][from.second];pieces[from.first][from.second]=null;selected=null}
            invalidate();return true
        }
    }
}
