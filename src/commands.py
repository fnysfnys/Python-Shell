from parser import Parser
from call_evaluator import CommandSubstituitionVisitor
from call_evaluator import CallTreeVisitor
from applications import execute_application
from command_interface import Command


class Call(Command):
    def __init__(self, raw_command):
        self.raw_command = raw_command

        self.application = None
        self.args = []
        self.file_output = None

    def _valid(self, out, call_tree):
        if not call_tree:
            if self.raw_command:
                out.append(f"Unrecognized Command: {self.raw_command}\n")
            return False
        return True

    def _eval_command_subsitution(self, out, call_tree):
        command_substituition_visitor = CommandSubstituitionVisitor(out)
        command_substituition_visitor.visit(call_tree)

    def _visit_call_tree(self, call_tree):
        """
        visits call tree and extracts application, arguments, and
        file output (if any).
        """
        call_tree_visitor = CallTreeVisitor()
        call_tree_visitor.visit_topdown(call_tree)

        self.application = call_tree_visitor.application
        self.args = call_tree_visitor.args
        self.file_output = call_tree_visitor.file_output

    def eval(self, out, in_pipe=False):
        parser = Parser()
        call_tree = parser.call_level_parse(self.raw_command)
        if not self._valid(out, call_tree):
            return
        else:
            self._eval_command_subsitution(out, call_tree)
            self._visit_call_tree(call_tree)
            if self.application:
                execute_application(self, out, in_pipe)


class PipeIterator:
    """
    Allows ordered iteration over all calls in a pipe
    """

    def _calls(self, pipe):
        calls = []
        while type(pipe.lhs()) is Pipe:
            calls.append(pipe.rhs())
            pipe = pipe.lhs()
        calls.append(pipe.rhs())
        calls.append(pipe.lhs())
        calls.reverse()
        return calls

    def __init__(self, pipe):
        self.index = 0
        self.calls = self._calls(pipe)

    def __next__(self):
        if self.index >= len(self.calls):
            raise StopIteration
        index = self.index
        self.index += 1
        return self.calls[index]


class Pipe(Command):

    """
    A Pipe is made up of Calls and/or other Pipes where:
        lhs = pipe | call
        rhs = call
    """

    def __init__(self, lhs, rhs):
        self.calls = (lhs, rhs)

    def lhs(self):
        return self.calls[0]

    def rhs(self):
        return self.calls[1]

    def __iter__(self):
        return PipeIterator(self)

    def eval(self, out):
        """
        For every command in a pipe, excluding the first, we take input from
        out as args by passing in in_pipe as true when evaluating each call
        """
        first_call = True
        for call in self:
            if first_call:
                call.eval(out)
                first_call = False
            else:
                call.eval(out, True)


class Seq(Command):
    def __init__(self, commands):
        self.commands = commands

    def eval(self, out):
        for commands in self.commands:
            commands.eval(out)
