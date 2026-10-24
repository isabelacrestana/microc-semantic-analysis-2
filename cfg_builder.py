"""Construa um CFG auxiliar por função, preservando os nós da AST."""

from __future__ import annotations

import load_previous  # Disponibiliza os módulos das etapas anteriores.

from ast_nodes import Block, BoolLiteral, FunctionDecl, IfStmt, ReturnStmt, Stmt, WhileStmt
from cfg import BlockId, Branch, CFG, Jump, Return, ScopeExit



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
            self.cfg.blocks[current].operations.append(ScopeExit(block.metadata["scope"]))

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

        true_block = self.cfg.new_block().id
        false_block = self.cfg.new_block().id

        self.cfg.terminate(current, Branch(condition=statement.condition, true_target=true_block, false_target=false_block))

        true_ending = self._build_statement(statement.then_block, true_block)

        if statement.else_block:
            false_ending = self._build_statement(statement.else_block, false_block)
        else: 
            false_ending = false_block

        if true_ending is None and false_ending is None:
            return None

        id_juncao = self.cfg.new_block().id
        
        if true_ending is not None:
            self.cfg.terminate(true_ending, Jump(target=id_juncao))

        if false_ending is not None:
            self.cfg.terminate(false_ending, Jump(target=id_juncao))

        return id_juncao


    def _build_while(self, statement: WhileStmt, current: BlockId) -> BlockId | None:
        """Construa o fluxo do laço e devolva sua continuação."""
        condition_block = self.cfg.new_block().id
        body_block = self.cfg.new_block().id
        self.cfg.terminate(current, Jump(target=condition_block))

        is_infinite = isinstance(statement.condition, BoolLiteral) and statement.condition.value is True

        if is_infinite:
            self.cfg.terminate(condition_block, Jump(target=body_block))
            end_body = self._build_statement(statement.body, body_block)
            if end_body is not None:
                self.cfg.terminate(end_body, Jump(target=condition_block))
            return None

        out_block = self.cfg.new_block().id
        self.cfg.terminate(
            condition_block,
            Branch(condition=statement.condition, true_target=body_block, false_target=out_block),
        )

        end_body = self._build_statement(statement.body, body_block)
        if end_body is not None:
            self.cfg.terminate(end_body, Jump(target=condition_block))

        return out_block

