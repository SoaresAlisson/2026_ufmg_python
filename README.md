# Introdução ao Python — XI Seminário Discente do Programa Pós Graduação Sociologia - UFMG

Oficina de 3 h: **lógica de programação para análise de dados**, com slides (Quarto/revealjs) e um notebook de 21 exercícios com **correção automática** no Google Colab. A base usada é o Cadastro Único da população de rua de Belo Horizonte.

## O que tem aqui

```
apresentacao.qmd / .html      slides (125 slides, revealjs)
partes/                       o conteúdo dos slides, por bloco
style.css                     identidade visual (vermelho UFMG, logo na capa)
img/                          logo da UFMG + QR code do notebook
exercicios/
  exercicio_python.qmd        fonte do notebook (enunciados + células)
  exercicio_python.ipynb      notebook para abrir no Colab
  corretor.py                 corretor automático (baixado pelo aluno)
  gabarito.py                 soluções do professor — NÃO vai ao GitHub
  poprua_cadunico_BH.csv      cópia local da base (o corretor lê este arquivo)
dados/                        base para o download no Colab
teste/
  gera_ipynb.py               regenera o .ipynb a partir do .qmd
  simulacao.py                valida corretor, gabarito, erros comuns e o .ipynb
roteiro_3h.md                 cronograma minuto a minuto + checklist do dia
```

## Como renderizar os slides

```bash
quarto render apresentacao.qmd
# abre apresentacao.html no navegador; os slides têm notas do apresentador (tecla S)
```

Para gerar um PDF de reserva (sem notas), abra `apresentacao.html?print-pdf` no Chrome e use "Imprimir → Salvar como PDF" com margens zero.

## Como regenerar o notebook

```bash
python3 teste/gera_ipynb.py      # .qmd -> .ipynb (limpa outputs, célula 0 = título)
python3 teste/simulacao.py       # roda os 4 cenários de teste (precisa de pandas/matplotlib)
```

A simulação deve terminar com `TUDO CERTO`: gabarito 10/10 nos 21 exercícios, modelos com `...` → 0, erros comuns → nota parcial ou 0, `.ipynb` consistente com o `.qmd`.

## Publicação no GitHub (para o Colab funcionar)

O notebook baixa `corretor.py` e o CSV por URL `raw`. Depois de criar o repositório `ufmg_intro_python` e dar o push:

```bash
git remote add origin git@github.com:SoaresAlisson/ufmg_intro_python.git
git push -u origin main
```

Conferir que as duas URLs respondem:

```bash
curl -sI https://raw.githubusercontent.com/SoaresAlisson/ufmg_intro_python/main/exercicios/corretor.py | head -1   # 200
curl -sI https://raw.githubusercontent.com/SoaresAlisson/ufmg_intro_python/main/dados/poprua_cadunico_BH.csv | head -1  # 200
curl -sI https://raw.githubusercontent.com/SoaresAlisson/ufmg_intro_python/main/exercicios/gabarito.py | head -1  # 404 (tem de dar 404)
```

O link que os alunos abrem é:

```
https://colab.research.google.com/github/SoaresAlisson/ufmg_intro_python/blob/main/exercicios/exercicio_python.ipynb
```

Se mudar o nome do repositório ou da pasta, atualize **três** lugares: a constante `BASE` na célula **Configuração** do `exercicio_python.qmd`, a mesma célula no `.ipynb` (basta regerar) e o QR code do slide 32.

## Como o corretor funciona

Cada exercício tem uma célula que começa com `# EXERCICIO n`. O corretor lê essa célula do histórico do notebook e corrige em um de quatro modos:

| Modo | Exercícios | O que faz |
|------|-----------|-----------|
| `variavel` | 1–9 | reexecuta a célula uma vez por caso de teste, injetando as entradas, e confere a variável-resposta |
| `funcao` | 10–11 | executa a célula e **chama a função** do aluno para cada caso |
| `importacao` | 12 | executa a célula e confere o DataFrame lido do CSV |
| `dataframe` | 13–21 | injeta `df_poprua` e roda checagens derivadas dos dados reais (nada de números fixos) |

Exercícios com método exigido (`query`, `groupby`, `.plot`) ou atalho proibido (`sum()` no exercício 8) são recusados com mensagem explicativa.

## Fonte dos dados

Cadastro Único da população em situação de rua — Prefeitura de Belo Horizonte:
<https://dados.pbh.gov.br/dataset/populacao-de-rua>
Cópia no repositório: 16.639 registros × 21 colunas (referência 07/2026).

## Licença e citação

Material didático do autor. Se usar, cite: SOARES, Alisson. *Introdução ao Python: lógica de programação para análise de dados*. XI Seminário Discente do PPGS-UFMG, Belo Horizonte, 2026.
