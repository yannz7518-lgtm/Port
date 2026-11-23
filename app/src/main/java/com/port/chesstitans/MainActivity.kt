package com.port.chesstitans

import android.app.Activity
import android.os.Bundle
import android.graphics.Color
import android.graphics.Typeface
import android.view.Gravity
import android.view.View
import android.widget.*

class MainActivity : Activity() {
    private val bg = Color.rgb(20, 31, 42)
    private val gold = Color.rgb(212, 175, 95)
    override fun onCreate(savedInstanceState: Bundle?) { super.onCreate(savedInstanceState); showMenu() }
    private fun showMenu() {
        val root = LinearLayout(this).apply { orientation=LinearLayout.VERTICAL; gravity=Gravity.CENTER; setBackgroundColor(bg); setPadding(28,24,28,24) }
        val title = TextView(this).apply { text="CHESS TITANS"; textSize=34f; setTextColor(gold); typeface=Typeface.create("serif",Typeface.BOLD); gravity=Gravity.CENTER }
        root.addView(title, LinearLayout.LayoutParams(-1,-2))
        val sub = TextView(this).apply { text="ANDROID PORT • DEVELOPMENT BUILD"; textSize=12f; setTextColor(Color.LTGRAY); gravity=Gravity.CENTER; setPadding(0,8,0,26) }
        root.addView(sub)
        addButton(root,"PLAY","Game engine integration is the next stage")
        addButton(root,"DIFFICULTY", "AI difficulty settings are not connected yet")
        addButton(root,"SETTINGS", "Settings will be added as the port develops")
        addButton(root,"EXIT", "Close application", true)
        setContentView(root)
    }
    private fun addButton(parent: LinearLayout, label:String, message:String, exit:Boolean=false) {
        val b=Button(this).apply { text=label; textSize=16f; setTextColor(Color.WHITE); setBackgroundColor(Color.rgb(46,65,82)); isAllCaps=true }
        val lp=LinearLayout.LayoutParams(300,54); lp.setMargins(0,7,0,7); parent.addView(b,lp)
        b.setOnClickListener { if(exit) finish() else Toast.makeText(this,message,Toast.LENGTH_SHORT).show() }
    }
}
