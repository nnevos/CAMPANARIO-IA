"""Regressao: perguntas "quem e X" nao podem ser inventadas nem recusadas sem motivo.

Usa fontes simuladas (sem rede). Nomes sao ficticios.
"""
import pytest

from campanario.chat.knowledge import natural_uncertainty, sourced_definition_answer
from campanario.utilities import integration
from campanario.utilities.web_chat import research_entity
from campanario.utilities.web_intent import direct_decision, short_entity_decision


# ---------------------------------------------------------------- decisao de pesquisar
@pytest.mark.parametrize('frase', [
    'quem é Marcos Vieira?',
    'quem foi Santos Dumont?',
    'quem era Marcos Vieira',
    'me fala sobre o Marcos Vieira',
    'fala um pouco sobre a Ana Souza',
    'conhece o Marcos Vieira?',
    'o que você sabe sobre Marcos Vieira',
    'você sabe algo sobre o Marcos Vieira?',
    'vocês conhecem o Marcos Vieira?',
])
def test_pergunta_sobre_pessoa_aciona_verificacao(frase):
    decisao = direct_decision(frase)
    assert decisao is not None and decisao.search, frase
    assert decisao.subject.endswith(('Vieira', 'Dumont', 'Souza')), decisao.subject


@pytest.mark.parametrize('frase', [
    'oi, tudo bem?',
    'me fala sobre jazz',
    'me conta da minha rotina',
    'me fala sobre a minha semana',
    'conhece alguma receita boa de bolo?',
    'você conhece um bom restaurante?',
])
def test_conversa_comum_nao_vira_busca_de_entidade(frase):
    decisao = direct_decision(frase)
    assert decisao is None or not decisao.search, frase


def test_assunto_nao_engole_o_verbo_ser():
    decisao = short_entity_decision('Marcos Vieira é cantor?')
    assert decisao is not None
    assert decisao.subject == 'Marcos Vieira'
    assert decisao.category == 'música'


# ---------------------------------------------------------------- portao de evidencia
class FakeUtil:
    def __init__(self, hits, pages):
        self.hits, self.pages = hits, pages

    def run(self, op, args):
        if op == 'web.search':
            if self.hits is None:
                return {'status': 'error', 'result': {'error': 'HTTP 403'}}
            return {'status': 'success', 'result': {'results': self.hits, 'provider': 'fake'}}
        page = self.pages.get(args['url'])
        if page is None:
            return {'status': 'error', 'result': {'error': 'HTTP 403'}}
        return {'status': 'success', 'result': page}


def wiki(title, body):
    url = 'https://pt.wikipedia.org/wiki/' + title.replace(' ', '_')
    page = {'title': title, 'url': url, 'content': body, 'read_method': 'wikipedia_summary',
            'read_at': '2026-11-19', 'source_id': '1'}
    return {'title': title, 'url': url, 'snippet': body[:80]}, url, page


def pesquisar(monkeypatch, subject, entradas, category=''):
    hits = [h for h, _, _ in entradas]
    pages = {u: p for _, u, p in entradas}
    monkeypatch.setattr(integration, 'service', lambda: FakeUtil(hits, pages))
    return research_entity(subject, subject=subject, category=category)


CANTOR = ('Marcos Vieira de Souza (Curitiba, 1980) é um cantor e compositor brasileiro, '
          'conhecido pelo álbum de estreia de 2005 e por turnês pelo país.')


def test_nome_curto_de_pessoa_real_com_um_unico_artigo_e_aceito(monkeypatch):
    # "pais" na biografia nao pode criar falsa ambiguidade.
    r = pesquisar(monkeypatch, 'Marcos Vieira', [wiki('Marcos Vieira de Souza', CANTOR)])
    assert r.status == 'grounded'
    assert r.read_count == 1


def test_titulo_identico_continua_aceito(monkeypatch):
    r = pesquisar(monkeypatch, 'Marcos Vieira', [wiki('Marcos Vieira', CANTOR)])
    assert r.status == 'grounded'


def test_dois_artigos_distintos_pedem_desambiguacao_com_candidatos(monkeypatch):
    jogador = ('Marcos Vieira Pereira (Recife, 1992) é um futebolista brasileiro que atua '
               'como zagueiro e disputou campeonatos nacionais.')
    r = pesquisar(monkeypatch, 'Marcos Vieira', [
        wiki('Marcos Vieira de Souza', CANTOR), wiki('Marcos Vieira Pereira', jogador)])
    assert r.status == 'ambiguous'
    assert set(r.candidates) == {'Marcos Vieira de Souza', 'Marcos Vieira Pereira'}
    texto = natural_uncertainty('morgana', r.subject, status=r.status, candidates=r.candidates)
    assert 'Marcos Vieira de Souza' in texto and 'Marcos Vieira Pereira' in texto


def test_nome_de_uma_palavra_nao_adivinha_pelo_prefixo(monkeypatch):
    corpo = 'Ana Maria Braga (Mairiporã, 1949) é uma apresentadora de televisão brasileira.'
    r = pesquisar(monkeypatch, 'Ana', [wiki('Ana Maria Braga', corpo)])
    assert r.status != 'grounded'


def test_titulo_com_parenteses_nao_autoriza_identidade_do_nome_nu(monkeypatch):
    corpo = 'Zeca é um personagem fictício de uma série de animação brasileira, muito popular.'
    r = pesquisar(monkeypatch, 'Zeca Lima', [wiki('Zeca Lima (personagem)', corpo)])
    assert r.status != 'grounded'


def test_falha_total_da_busca_continua_recusando_sem_inventar(monkeypatch):
    monkeypatch.setattr(integration, 'service', lambda: FakeUtil(None, {}))
    r = research_entity('Marcos Vieira', subject='Marcos Vieira')
    assert r.status == 'failed' and r.requires_abstention


def test_resposta_extraida_para_nome_curto_cita_a_fonte(monkeypatch):
    r = pesquisar(monkeypatch, 'Marcos Vieira', [wiki('Marcos Vieira de Souza', CANTOR)])
    resposta = sourced_definition_answer('morgana', r, 'quem é Marcos Vieira?')
    assert resposta is not None
    assert 'cantor e compositor' in resposta
    assert 'pt.wikipedia.org/wiki/Marcos_Vieira_de_Souza' in resposta
