
from core.codebase_reader import CodebaseReader

def register(dispatcher):
    reader = CodebaseReader()
    dispatcher.register("reader", reader.handle_reader)
    dispatcher.register("search code", reader.handle_reader)
    dispatcher.register("list project files", reader.handle_reader)
    dispatcher.register("explain code", reader.handle_reader)
