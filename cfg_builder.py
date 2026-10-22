"""Construa um CFG auxiliar por função, preservando os nós da AST."""

from __future__ import annotations

import load_previous  # Disponibiliza os módulos das etapas anteriores.

from ast_nodes import Block, FunctionDecl, IfStmt, Stmt, WhileStmt, ReturnStmt
from cfg import BlockId, CFG, Jump, ScopeExit, Return, Branch



class CFGBuilder:
    def build(self, function: FunctionDecl) -> CFG:
        self.cfg = CFG(function)
        body_entry = self.cfg.new_block()
        self.cfg.terminate(self.cfg.entry, Jump(body_entry.id))
        continuation = self._build_block(function.body, body_entry.id)
        if continuation is not None:
            self.cfg.terminate(continuation, Jump(self.cfg.fallthrough_exit))
        return self.cfg

    def _build_block(self, block: Block, current: BlockId) -> BlockId | None:
        """Percorra um bloco da AST e devolva sua continuação normal.

        `current` identifica um bloco básico aberto. Comandos sequenciais
        permanecem nele. Comandos de controle podem mudar a continuação.
        None indica que os caminhos deste bloco não alcançam o próximo comando.
        """

        for statement in block.statements:
            if current is None:
                break

            current = self._build_statement(statement, current)

        if current is not None:
            self.cfg.blocks[current].operations.append(ScopeExit(block.scope))

        return current
    

    def _build_statement(self, statement: Stmt, current: BlockId) -> BlockId | None:
        """TODO: incorpore um comando ao CFG e devolva sua continuação normal."""

        if current is None:
            return current

        if isinstance(statement, Block):
            return self._build_block(statement, current)

        elif isinstance(statement, IfStmt):
            return self._build_if(statement, current)

        elif isinstance(statement, WhileStmt):
            return self._build_while(statement, current)

        elif isinstance(statement, ReturnStmt):
            self.cfg.terminate(current, Return(statement=statement))
            return None
        
        else:
            self.cfg.blocks[current].operations.append(statement)
            return current



    def _build_if(self, statement: IfStmt, current: BlockId) -> BlockId | None:
        """TODO: construa o fluxo da condicional e devolva sua continuação."""

        id_verdadeiro = self.cfg.new_block().id
        id_falso = self.cfg.new_block().id

        self.cfg.terminate(current, Branch(condition=statement.condition, true_target=id_verdadeiro, false_target=id_falso))

        fim_verdadeiro = self._build_statement(statement.then_block, id_verdadeiro)

        if statement.else_block:
            fim_falso = self._build_statement(statement.else_block, id_falso)
        else: 
            fim_falso = id_falso

        if fim_verdadeiro is None and fim_falso is None:
            return None

        id_juncao = self.cfg.new_block().id
        
        if fim_verdadeiro is not None:
            self.cfg.terminate(fim_verdadeiro, Jump(target=id_juncao))

        if fim_falso is not None:
            self.cfg.terminate(fim_falso, Jump(target=id_juncao))

        return id_juncao


    def _build_while(self, statement: WhileStmt, current: BlockId) -> BlockId | None:
        """TODO: construa o fluxo do laço e devolva sua continuação."""

        raise NotImplementedError("implemente CFGBuilder._build_while")
