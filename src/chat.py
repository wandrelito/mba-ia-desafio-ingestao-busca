"""Interface de linha de comando para perguntas sobre o PDF."""
from search import responder_pergunta


def main():
    print('Chat com PDF. Digite sair para encerrar.')
    while True:
        try:
            pergunta = input('\nFaça sua pergunta: ').strip()
        except (EOFError, KeyboardInterrupt):
            print('\nAté logo!')
            break
        if pergunta.lower() in {'sair', 'exit', 'quit'}:
            break
        if not pergunta:
            continue
        try:
            print(f'RESPOSTA: {responder_pergunta(pergunta)}')
        except Exception as erro:
            print(f'Erro ao consultar: {erro}')


if __name__ == '__main__':
    main()
