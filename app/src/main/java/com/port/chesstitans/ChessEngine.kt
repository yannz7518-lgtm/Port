package com.port.chesstitans

class ChessEngine {
    val board = Array(8) { CharArray(8) { '.' } }
    var whiteToMove = true
    var enPassant: Pair<Int,Int>? = null
    var status = "White to move"
    private var whiteKingSide=true; private var whiteQueenSide=true
    private var blackKingSide=true; private var blackQueenSide=true
    private var halfmoveClock=0
    private val history=mutableListOf<State>()
    private val repetition=mutableMapOf<String,Int>()
    data class Move(val fr:Int,val fc:Int,val tr:Int,val tc:Int,val promotion:Char?=null,val castle:Boolean=false,val ep:Boolean=false)
    private data class State(val squares:Array<CharArray>,val ep:Pair<Int,Int>?,val white:Boolean,val status:String,val wk:Boolean,val wq:Boolean,val bk:Boolean,val bq:Boolean,val half:Int,val key:String)

    init { reset() }
    fun reset(){
        val back="rnbqkbnr"
        for(r in 0..7)for(c in 0..7)board[r][c]='.'
        for(c in 0..7){board[0][c]=back[c];board[1][c]='p';board[6][c]='P';board[7][c]=back[c].uppercaseChar()}
        whiteToMove=true;enPassant=null;status="White to move"
        whiteKingSide=true;whiteQueenSide=true;blackKingSide=true;blackQueenSide=true;halfmoveClock=0
        history.clear();repetition.clear();repetition[key()]=1
    }
    fun legalMoves(r:Int,c:Int):List<Move>{
        if(r !in 0..7||c !in 0..7)return emptyList()
        val p=board[r][c];if(p=='.'||isWhite(p)!=whiteToMove)return emptyList()
        return pseudo(r,c).filter{m->val s=snapshot();applyRaw(m);val safe=!inCheck(whiteToMove);restore(s);safe}
    }
    fun allLegal():List<Move> =(0..7).flatMap{r->(0..7).flatMap{c->legalMoves(r,c)}}
    fun play(m:Move):Boolean{
        if(m !in legalMoves(m.fr,m.fc))return false
        history.add(snapshot());applyRaw(m);whiteToMove=!whiteToMove
        val k=key();repetition[k]=(repetition[k]?:0)+1
        updateStatus();return true
    }
    fun undo():Boolean{
        if(history.isEmpty())return false
        val cur=key();repetition[cur]=(repetition[cur]?:1)-1;if(repetition[cur]<=0)repetition.remove(cur)
        restore(history.removeAt(history.lastIndex));updateStatus();return true
    }
    fun computerMove(level:Int=1):Boolean{
        val moves=allLegal();if(moves.isEmpty())return false
        val depth=when(level){1->1;else->2}
        var best:Move?=null;var bestScore=if(whiteToMove)Int.MIN_VALUE else Int.MAX_VALUE
        for(m in moves){val s=snapshot();applyRaw(m);whiteToMove=!whiteToMove;val score=search(depth-1,-100000,100000);restore(s)
            val adjusted=score+(if(center(m.tr,m.tc))if(whiteToMove)3 else -3 else 0)
            if(whiteToMove&&adjusted>bestScore||!whiteToMove&&adjusted<bestScore){bestScore=adjusted;best=m}}
        return best?.let{play(it)}?:false
    }
    private fun search(depth:Int,alpha0:Int,beta0:Int):Int{
        val moves=allLegal()
        if(moves.isEmpty())return if(inCheck(whiteToMove)){if(whiteToMove)-90000+depth else 90000-depth}else 0
        if(depth<=0)return evaluate()
        var alpha=alpha0;var beta=beta0
        if(whiteToMove){var best=-100000;for(m in moves){val s=snapshot();applyRaw(m);whiteToMove=false;val v=search(depth-1,alpha,beta);restore(s);best=maxOf(best,v);alpha=maxOf(alpha,best);if(beta<=alpha)break};return best}
        else{var best=100000;for(m in moves){val s=snapshot();applyRaw(m);whiteToMove=true;val v=search(depth-1,alpha,beta);restore(s);best=minOf(best,v);beta=minOf(beta,best);if(beta<=alpha)break};return best}
    }
    private fun evaluate():Int{var score=0;for(r in 0..7)for(c in 0..7){val p=board[r][c];if(p!='.')score+=(if(p.isUpperCase())1 else -1)*pieceValue(p)*100+(if(center(r,c))if(p.isUpperCase())8 else -8 else 0)};return score}
    private fun center(r:Int,c:Int)=r in 2..5&&c in 2..5
    private fun pieceValue(p:Char)=when(p.lowercaseChar()){'q'->9;'r'->5;'b','n'->3;'p'->1;else->0}
    private fun isWhite(p:Char)=p.isUpperCase()
    private fun pseudo(r:Int,c:Int):List<Move>{
        val p=board[r][c];val w=isWhite(p);val out=mutableListOf<Move>();val dir=if(w)-1 else 1
        fun add(nr:Int,nc:Int){if(nr in 0..7&&nc in 0..7&&(board[nr][nc]=='.'||isWhite(board[nr][nc])!=w)&&board[nr][nc].lowercaseChar()!='k')out.add(Move(r,c,nr,nc))}
        when(p.lowercaseChar()){
            'p'->{val nr=r+dir
                if(nr in 0..7&&board[nr][c]=='.'){out.add(Move(r,c,nr,c,if(nr==0||nr==7)if(w)'Q' else 'q' else null));if((w&&r==6||!w&&r==1)&&board[r+2*dir][c]=='.')out.add(Move(r,c,r+2*dir,c))}
                for(dc in -1..1 step 2){val nc=c+dc;if(nr in 0..7&&nc in 0..7){if(board[nr][nc]!='.'&&isWhite(board[nr][nc])!=w&&board[nr][nc].lowercaseChar()!='k')out.add(Move(r,c,nr,nc,if(nr==0||nr==7)if(w)'Q' else 'q' else null));if(enPassant==Pair(nr,nc))out.add(Move(r,c,nr,nc,ep=true))}}
            }
            'n'->for((dr,dc) in knightSteps)add(r+dr,c+dc)
            'k'->{for(dr in -1..1)for(dc in -1..1)if(dr!=0||dc!=0)add(r+dr,c+dc)
                if(w&&r==7&&c==4){if(whiteKingSide&&board[7][7]=='R'&&board[7][5]=='.'&&board[7][6]=='.'&&!inCheck(true)&&!attacked(7,5,false)&&!attacked(7,6,false))out.add(Move(7,4,7,6,castle=true));if(whiteQueenSide&&board[7][0]=='R'&&board[7][1]=='.'&&board[7][2]=='.'&&board[7][3]=='.'&&!inCheck(true)&&!attacked(7,3,false)&&!attacked(7,2,false))out.add(Move(7,4,7,2,castle=true))}
                if(!w&&r==0&&c==4){if(blackKingSide&&board[0][7]=='r'&&board[0][5]=='.'&&board[0][6]=='.'&&!inCheck(false)&&!attacked(0,5,true)&&!attacked(0,6,true))out.add(Move(0,4,0,6,castle=true));if(blackQueenSide&&board[0][0]=='r'&&board[0][1]=='.'&&board[0][2]=='.'&&board[0][3]=='.'&&!inCheck(false)&&!attacked(0,3,true)&&!attacked(0,2,true))out.add(Move(0,4,0,2,castle=true))}
            }
            else->{val dirs=when(p.lowercaseChar()){'b'->bishopDirs;'r'->rookDirs;else->bishopDirs+rookDirs};for((dr,dc) in dirs){var nr=r+dr;var nc=c+dc;while(nr in 0..7&&nc in 0..7){if(board[nr][nc]=='.')out.add(Move(r,c,nr,nc))else{if(isWhite(board[nr][nc])!=w&&board[nr][nc].lowercaseChar()!='k')out.add(Move(r,c,nr,nc));break};nr+=dr;nc+=dc}}}
        };return out
    }
    private val knightSteps=listOf(-2 to -1,-2 to 1,-1 to -2,-1 to 2,1 to -2,1 to 2,2 to -1,2 to 1)
    private val bishopDirs=listOf(-1 to -1,-1 to 1,1 to -1,1 to 1)
    private val rookDirs=listOf(-1 to 0,1 to 0,0 to -1,0 to 1)
    private fun attacked(r:Int,c:Int,byWhite:Boolean):Boolean{
        val pawn=if(byWhite)'P' else 'p';val pr=r+(if(byWhite)1 else -1)
        for(pc in c-1..c+1 step 2)if(pr in 0..7&&pc in 0..7&&board[pr][pc]==pawn)return true
        val n=if(byWhite)'N' else 'n';for((dr,dc) in knightSteps){val rr=r+dr;val cc=c+dc;if(rr in 0..7&&cc in 0..7&&board[rr][cc]==n)return true}
        for(dr in -1..1)for(dc in -1..1)if(dr!=0||dc!=0){val rr=r+dr;val cc=c+dc;if(rr in 0..7&&cc in 0..7&&board[rr][cc]==if(byWhite)'K' else 'k')return true}
        for((dr,dc) in bishopDirs+rookDirs){var rr=r+dr;var cc=c+dc;var step=1;while(rr in 0..7&&cc in 0..7){val x=board[rr][cc];if(x!='.'){if(isWhite(x)==byWhite&&(x.lowercaseChar()=='q'||(step==1&&x.lowercaseChar()=='k')||((dr==0||dc==0)&&x.lowercaseChar()=='r')||(dr!=0&&dc!=0&&x.lowercaseChar()=='b')))return true;break};rr+=dr;cc+=dc;step++}}
        return false
    }
    private fun inCheck(w:Boolean):Boolean{val king=if(w)'K' else 'k';for(r in 0..7)for(c in 0..7)if(board[r][c]==king)return attacked(r,c,!w);return true}
    private fun applyRaw(m:Move){
        val p=board[m.fr][m.fc];val captured=board[m.tr][m.tc]
        if(p=='K'){whiteKingSide=false;whiteQueenSide=false};if(p=='k'){blackKingSide=false;blackQueenSide=false}
        if(p=='R'&&m.fr==7&&m.fc==0)whiteQueenSide=false;if(p=='R'&&m.fr==7&&m.fc==7)whiteKingSide=false
        if(p=='r'&&m.fr==0&&m.fc==0)blackQueenSide=false;if(p=='r'&&m.fr==0&&m.fc==7)blackKingSide=false
        if(captured=='R'&&m.tr==7&&m.tc==0)whiteQueenSide=false;if(captured=='R'&&m.tr==7&&m.tc==7)whiteKingSide=false
        if(captured=='r'&&m.tr==0&&m.tc==0)blackQueenSide=false;if(captured=='r'&&m.tr==0&&m.tc==7)blackKingSide=false
        board[m.fr][m.fc]='.';if(m.ep)board[m.fr][m.tc]='.';board[m.tr][m.tc]=m.promotion?:p
        if(m.castle){if(m.tc==6){board[m.tr][5]=board[m.tr][7];board[m.tr][7]='.'}else{board[m.tr][3]=board[m.tr][0];board[m.tr][0]='.'}}
        halfmoveClock=if(p.lowercaseChar()=='p'||captured!='.')0 else halfmoveClock+1
        enPassant=if(p.lowercaseChar()=='p'&&kotlin.math.abs(m.tr-m.fr)==2)Pair((m.tr+m.fr)/2,m.fc)else null
    }
    private fun updateStatus(){
        val moves=allLegal();status=when{moves.isEmpty()&&inCheck(whiteToMove)->if(whiteToMove)"Checkmate — Black wins" else "Checkmate — White wins";moves.isEmpty()->"Stalemate";(repetition[key()] ?: 0)>=3->"Draw — threefold repetition";halfmoveClock>=100->"Draw — 50-move rule";insufficientMaterial()->"Draw — insufficient material";inCheck(whiteToMove)->if(whiteToMove)"White in check" else "Black in check";else->if(whiteToMove)"White to move" else "Black to move"}
    }
    private fun insufficientMaterial():Boolean{val pieces=mutableListOf<Pair<Char,Pair<Int,Int>>>();for(r in 0..7)for(c in 0..7){val p=board[r][c];if(p!='.'&&p.lowercaseChar()!='k')pieces.add(p to (r to c))};if(pieces.isEmpty())return true;if(pieces.size==1&&pieces[0].first.lowercaseChar() in listOf('b','n'))return true;if(pieces.all{it.first.lowercaseChar()=='b'}){val colors=pieces.map{(r,c)->(r+c)%2}.distinct();return colors.size==1};return false}
    private fun key():String=board.joinToString(""){String(it)}+"|"+whiteToMove+"|"+whiteKingSide+whiteQueenSide+blackKingSide+blackQueenSide+"|"+enPassant
    private fun snapshot()=State(board.map{it.copyOf()}.toTypedArray(),enPassant,whiteToMove,status,whiteKingSide,whiteQueenSide,blackKingSide,blackQueenSide,halfmoveClock,key())
    private fun restore(s:State){for(r in 0..7)board[r]=s.squares[r].copyOf();enPassant=s.ep;whiteToMove=s.white;status=s.status;whiteKingSide=s.wk;whiteQueenSide=s.wq;blackKingSide=s.bk;blackQueenSide=s.bq;halfmoveClock=s.half}
}
