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
        game.board[7][4]='K';game.board[0][0]='k';game.board[0][4]='r'
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
    @Test fun castlingMovesRookAndKing(){
        val game=ChessEngine()
        for(r in 0..7)for(c in 0..7)game.board[r][c]='.'
        game.board[7][4]='K';game.board[7][7]='R';game.board[0][4]='k';game.whiteToMove=true
        val castle=game.legalMoves(7,4).firstOrNull{it.castle&&it.tc==6}
        assertNotNull(castle);assertTrue(game.play(castle!!))
        assertEquals('K',game.board[7][6]);assertEquals('R',game.board[7][5]);assertEquals('.',game.board[7][7])
    }
    @Test fun enPassantCaptureRemovesPawn(){
        val game=ChessEngine()
        assertTrue(game.play(ChessEngine.Move(6,4,4,4)))
        assertTrue(game.play(ChessEngine.Move(1,0,2,0)))
        assertTrue(game.play(ChessEngine.Move(4,4,3,4)))
        assertTrue(game.play(ChessEngine.Move(1,3,3,3)))
        val ep=game.legalMoves(3,4).firstOrNull{it.ep&&it.tr==2&&it.tc==3}
        assertNotNull(ep);assertTrue(game.play(ep!!))
        assertEquals('P',game.board[2][3]);assertEquals('.',game.board[3][3])
    }
}
