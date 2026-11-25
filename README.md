# Introdução ao Python — XI Seminário Discente do Programa Pós Graduação Sociologia - UFMG

Oficina de 3 h: **lógica de programação para análise de dados**, com slides (Quarto/revealjs) e um notebook de 21 exercícios com **correção automática** no Google Colab. A base usada é o Cadastro Único da população de rua de Belo Horizonte.

Link para apresentação: <https://soaresalisson.github.io/2026_ufmg_python/>

O link que os alunos abrem é:

```
https://colab.research.google.com/github/SoaresAlisson/2026_ufmg_python/blob/main/exercicios/exercicio_python.ipynb
```

Se mudar o nome do repositório ou da pasta, atualize **três** lugares: a constante `BASE` na célula **Configuração** do `exercicio_python.qmd`, a mesma célula no `.ipynb` (basta regerar) e o QR code do slide 32.

## Fonte dos dados

Cadastro Único da população em situação de rua — Prefeitura de Belo Horizonte:
<https://dados.pbh.gov.br/dataset/populacao-de-rua>
Cópia no repositório: 16.639 registros × 21 colunas (referência 07/2026).

## Publicação (GitHub Pages)

O site é gerado em `docs/` (config em `_quarto.yml`, `output-dir: docs`, `embed-resources: true`):

```bash
export PATH=/usr/lib/rstudio/resources/app/bin/quarto/bin:$PATH
quarto render        # gera docs/index.html autossuficiente
```

No GitHub: **Settings → Pages → Deploy from branch** → `main`, pasta `/docs`.
Site: <https://SoaresAlisson.github.io/2026_ufmg_python/>.

## Licença e citação

Material didático do autor. Se usar, cite: SOARES, Alisson. *Introdução ao Python: lógica de programação para análise de dados*. XI Seminário Discente do PPGS-UFMG, Belo Horizonte, 2026.
