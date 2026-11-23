package com.port.chesstitans

class ChessEngine {
    // White pieces uppercase, black lowercase. Empty squares are '.'
    val board = Array(8) { CharArray(8) { '.' } }
    var whiteToMove = true
    var enPassant: Pair<Int,Int>? = null
    var status = "White to move"
    private val history=mutableListOf<Array<Any>>()
    data class Move(val fr:Int,val fc:Int,val tr:Int,val tc:Int,val promotion:Char?=null,val castle:Boolean=false,val ep:Boolean=false)

    init { reset() }
    fun reset() {
        val back="rnbqkbnr"
        for(c in 0..7){board[0][c]=back[c];board[1][c]='p';board[6][c]='P';board[7][c]=back[c].uppercaseChar()}
        whiteToMove=true; enPassant=null; status="White to move"; history.clear()
    }
    fun legalMoves(r:Int,c:Int):List<Move> {
        val p=board[r][c]; if(p=='.'||isWhite(p)!=whiteToMove)return emptyList()
        return pseudo(r,c).filter { m -> val copy=snapshot(); applyRaw(m); val safe=!inCheck(whiteToMove); restore(copy); safe }
    }
    fun allLegal():List<Move> = (0..7).flatMap{r->(0..7).flatMap{c->legalMoves(r,c)}}
    fun play(m:Move):Boolean {
        if(m !in legalMoves(m.fr,m.fc))return false
        history.add(snapshot()); applyRaw(m); whiteToMove=!whiteToMove
        val moves=allLegal()
        status=when { moves.isEmpty() && inCheck(whiteToMove) -> if(whiteToMove) "Checkmate — Black wins" else "Checkmate — White wins"
            moves.isEmpty() -> "Stalemate"; inCheck(whiteToMove)->if(whiteToMove) "White in check" else "Black in check"
            else -> if(whiteToMove) "White to move" else "Black to move" }
        return true
    }
    fun undo():Boolean { if(history.isEmpty())return false; restore(history.removeAt(history.lastIndex)); status=if(whiteToMove) "White to move" else "Black to move"; return true }
    fun computerMove():Boolean { val moves=allLegal(); if(moves.isEmpty())return false
        // Prefer captures, checks, and central moves; deterministic light-weight evaluation.
        val chosen=moves.maxByOrNull { m -> (if(board[m.tr][m.tc]!='.')value(board[m.tr][m.tc])*10 else 0)+(if(center(m.tr,m.tc))2 else 0)+(if(m.promotion!=null)80 else 0) }!!
        return play(chosen)
    }
    private fun center(r:Int,c:Int)=r in 2..5&&c in 2..5
    private fun value(p:Char)=when(p.lowercaseChar()){'q'->9;'r'->5;'b','n'->3;'p'->1;else->0}
    private fun isWhite(p:Char)=p.isUpperCase()
    private fun pseudo(r:Int,c:Int):List<Move>{
        val p=board[r][c]; val w=isWhite(p); val out=mutableListOf<Move>(); val dir=if(w)-1 else 1
        fun add(nr:Int,nc:Int){if(nr in 0..7&&nc in 0..7&&(board[nr][nc]=='.'||isWhite(board[nr][nc])!=w))out.add(Move(r,c,nr,nc))}
        when(p.lowercaseChar()){
            'p'->{val nr=r+dir;if(nr in 0..7&&board[nr][c]=='.'){out.add(Move(r,c,nr,c,if(nr==0||nr==7)if(w)'Q' else 'q' else null));if((w&&r==6||!w&&r==1)&&board[r+2*dir][c]=='.')out.add(Move(r,c,r+2*dir,c))}
                for(dc in listOf(-1,1)){val nc=c+dc;if(nr in 0..7&&nc in 0..7&&board[nr][nc]!='.'&&isWhite(board[nr][nc])!=w)out.add(Move(r,c,nr,nc,if(nr==0||nr==7)if(w)'Q' else 'q' else null));if(enPassant==Pair(nr,nc))out.add(Move(r,c,nr,nc,ep=true))}
            }
            'n'->for((dr,dc) in listOf(-2 to -1,-2 to 1,-1 to -2,-1 to 2,1 to -2,1 to 2,2 to -1,2 to 1))add(r+dr,c+dc)
            'k'->{for(dr in -1..1)for(dc in -1..1)if(dr!=0||dc!=0)add(r+dr,c+dc)
                if(w&&r==7&&c==4){if(board[7][7]=='R'&&board[7][5]=='.'&&board[7][6]=='.'&&!inCheck(true)&&!attacked(7,5,false)&&!attacked(7,6,false))out.add(Move(7,4,7,6,castle=true));if(board[7][0]=='R'&&board[7][1]=='.'&&board[7][2]=='.'&&board[7][3]=='.'&&!inCheck(true)&&!attacked(7,3,false)&&!attacked(7,2,false))out.add(Move(7,4,7,2,castle=true))}
                if(!w&&r==0&&c==4){if(board[0][7]=='r'&&board[0][5]=='.'&&board[0][6]=='.'&&!inCheck(false)&&!attacked(0,5,true)&&!attacked(0,6,true))out.add(Move(0,4,0,6,castle=true));if(board[0][0]=='r'&&board[0][1]=='.'&&board[0][2]=='.'&&board[0][3]=='.'&&!inCheck(false)&&!attacked(0,3,true)&&!attacked(0,2,true))out.add(Move(0,4,0,2,castle=true))}
            }
            else->{val dirs=if(p.lowercaseChar()=='b')listOf(-1 to -1,-1 to 1,1 to -1,1 to 1) else if(p.lowercaseChar()=='r')listOf(-1 to 0,1 to 0,0 to -1,0 to 1) else listOf(-1 to -1,-1 to 1,1 to -1,1 to 1,-1 to 0,1 to 0,0 to -1,0 to 1)
                for((dr,dc) in dirs){var nr=r+dr;var nc=c+dc;while(nr in 0..7&&nc in 0..7){if(board[nr][nc]=='.')out.add(Move(r,c,nr,nc))else{if(isWhite(board[nr][nc])!=w)out.add(Move(r,c,nr,nc));break};nr+=dr;nc+=dc}}
            }
        };return out
    }
    private fun attacked(r:Int,c:Int,byWhite:Boolean):Boolean {
        val pawn=if(byWhite)'P' else 'p';val pr=r+(if(byWhite)1 else -1)
        for(pc in c-1..c+1 step 2)if(pr in 0..7&&pc in 0..7&&board[pr][pc]==pawn)return true
        val knight=if(byWhite)'N' else 'n';for((dr,dc) in listOf(-2 to -1,-2 to 1,-1 to -2,-1 to 2,1 to -2,1 to 2,2 to -1,2 to 1)){val rr=r+dr;val cc=c+dc;if(rr in 0..7&&cc in 0..7&&board[rr][cc]==knight)return true}
        for(dr in -1..1)for(dc in -1..1)if(dr!=0||dc!=0){val rr=r+dr;val cc=c+dc;if(rr in 0..7&&cc in 0..7&&board[rr][cc]==if(byWhite)'K' else 'k')return true}
        for((dr,dc) in listOf(-1 to 0,1 to 0,0 to -1,0 to 1,-1 to -1,-1 to 1,1 to -1,1 to 1)){var rr=r+dr;var cc=c+dc;var step=1;while(rr in 0..7&&cc in 0..7){val x=board[rr][cc];if(x!='.'){if(isWhite(x)==byWhite&&(x.lowercaseChar()=='q'||(step==1&&x.lowercaseChar()=='k')||((dr==0||dc==0)&&x.lowercaseChar()=='r')||(dr!=0&&dc!=0&&x.lowercaseChar()=='b')))return true;break};rr+=dr;cc+=dc;step++}}
        return false
    }
    private fun inCheck(w:Boolean):Boolean{val k=if(w)'K' else 'k';for(r in 0..7)for(c in 0..7)if(board[r][c]==k)return attacked(r,c,!w);return true}
    private fun applyRaw(m:Move){val p=board[m.fr][m.fc];board[m.fr][m.fc]='.';if(m.ep)board[m.fr][m.tc]='.';board[m.tr][m.tc]=m.promotion?:p
        if(m.castle){if(m.tc==6){board[m.tr][5]=board[m.tr][7];board[m.tr][7]='.'}else{board[m.tr][3]=board[m.tr][0];board[m.tr][0]='.'}}
        enPassant=if(p.lowercaseChar()=='p'&&kotlin.math.abs(m.tr-m.fr)==2)Pair((m.tr+m.fr)/2,m.fc)else null}
    private fun snapshot():Array<Any>{return arrayOf(board.map{it.copyOf()}.toTypedArray(),enPassant,whiteToMove,status)}
    private fun restore(s:Array<Any>){val b=s[0] as Array<CharArray>;for(r in 0..7)board[r]=b[r].copyOf();enPassant=s[1] as Pair<Int,Int>?; if(s.size>2){whiteToMove=s[2] as Boolean;status=s[3] as String}}
}
