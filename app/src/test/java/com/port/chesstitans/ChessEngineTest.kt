package com.port.chesstitans

import org.junit.Assert.*
import org.junit.Test

class ChessEngineTest {
    @Test fun initialPositionHasTwentyLegalMoves(){
        val game=ChessEngine()
        assertEquals(20,game.allLegal().size)
        assertEquals(2,game.legalMoves(6,4).size)
    }
    @Test fun normalMovesAndUndoRestoreBoardAndTurn(){
        val game=ChessEngine()
        assertTrue(game.play(ChessEngine.Move(6,4,4,4)))
        assertEquals('P',game.board[4][4]);assertFalse(game.whiteToMove)
        assertTrue(game.play(ChessEngine.Move(1,4,3,4)))
        assertEquals('p',game.board[3][4]);assertTrue(game.whiteToMove)
        assertTrue(game.undo());assertEquals('.',game.board[3][4]);assertFalse(game.whiteToMove)
        assertTrue(game.undo());assertEquals('.',game.board[4][4]);assertTrue(game.whiteToMove)
    }
    @Test fun cannotMoveIntoCheck(){
        val game=ChessEngine()
        for(r in 0..7)for(c in 0..7)game.board[r][c]='.'
        game.board[7][4]='K';game.board[0][4]='k';game.board[0][0]='r'
        game.whiteToMove=true
        assertFalse(game.legalMoves(7,4).any{it.tr==6&&it.tc==4})
    }
    @Test fun promotionIsAutomaticQueen(){
        val game=ChessEngine()
        for(r in 0..7)for(c in 0..7)game.board[r][c]='.'
        game.board[7][4]='K';game.board[0][4]='k';game.board[1][0]='P'
        game.whiteToMove=true
        val promotion=game.legalMoves(1,0).first{it.tr==0&&it.tc==0}
        assertEquals('Q',promotion.promotion)
        assertTrue(game.play(promotion));assertEquals('Q',game.board[0][0])
    }
}
