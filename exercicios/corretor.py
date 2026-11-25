# =====================================================================
#  CORRETOR AUTOMATICO — XI Seminário Discente do PPGS-UFMG
#  "Introdução ao Python: lógica de programação para análise de dados"
#
#  Como usar no notebook/Colab:
#      from corretor import avaliar, verificar_preenchimento_questoes
#      avaliar(1) ... avaliar(21)              # corrige o exercício n
#      verificar_preenchimento_questoes()     # confere tudo + nome
#
#  Este arquivo é baixado pela célula "Configuração" do notebook.
# =====================================================================
#
#  COMO FUNCIONA (para quem quiser ler o código):
#  - O corretor procura no histórico do notebook a última célula que
#    começa com o marcador "# EXERCICIO <n>".
#  - Quatro modos de correção, um por exercício:
#      variavel   -> roda o código uma vez por caso de teste, injetando
#                    as variáveis de entrada, e confere a variável-resposta.
#      funcao     -> executa a célula uma única vez e CHAMA a função do
#                    aluno para cada caso, conferindo o valor devolvido.
#      importacao -> executa a célula e confere o DataFrame lido do CSV.
#      dataframe  -> injeta df_poprua (lido do CSV local) e roda checagens
#                    semânticas sobre a variável-resposta, derivadas dos
#                    dados reais (nada de números fixos no código).
#  - Exercícios com método exigido (query, groupby, agg, plot) são
#    recusados se o método não aparecer no código do aluno.
# =====================================================================

import copy
import re

TOLERANCIA = 0.01  # aceita diferenças de arredondamento
ARQUIVO_CSV = "poprua_cadunico_BH.csv"

_df_cache = None


# ---------------------------------------------------------------------
#  Base de dados (usada nos exercícios de pandas)
# ---------------------------------------------------------------------


def _pd():
    """Importa o pandas só quando algum exercício precisa dele."""
    import pandas as pd  # noqa: F401  (import tardio de propósito)

    return pd


def _carregar_df(imprimir=True):
    """Lê o CSV da população de rua de BH (o mesmo que o aluno baixou)."""
    global _df_cache
    if _df_cache is not None:
        return _df_cache
    pd = _pd()
    try:
        _df_cache = pd.read_csv(ARQUIVO_CSV)
        return _df_cache
    except FileNotFoundError:
        if imprimir:
            print(
                f"  [FALHOU] Não encontrei o arquivo '{ARQUIVO_CSV}' no diretório"
                " do notebook."
            )
            print("           Rode antes a célula de download da Configuração.")
        return None
    except Exception as erro:
        if imprimir:
            print(f"  [FALHOU] Não consegui ler '{ARQUIVO_CSV}': {erro}")
        return None


# ---------------------------------------------------------------------
#  Histórico do notebook
# ---------------------------------------------------------------------


def pega_codigo_aluno(n):
    """Encontra no histórico do notebook a última célula do exercício n."""
    ip = get_ipython()
    marcador = "# EXERCICIO " + str(n)
    for celula in reversed(ip.history_manager.input_hist_parsed):
        if celula.split("\n", 1)[0].strip() == marcador:
            return celula
    return None


def tem_pontinhos(codigo):
    """True se ainda há '...' no código do aluno (ignorando comentários)."""
    for linha in codigo.splitlines():
        trecho = re.sub(r"#.*$", "", linha)
        if "..." in trecho:
            return True
    return False


def prepara_codigo(codigo, entradas):
    """Retira do código do aluno as linhas que definem as variáveis de entrada.

    O corretor injeta os valores de teste no lugar delas — o valor de
    exemplo que o aluno deixou na célula nunca entra na correção.
    """
    if not entradas:
        return codigo
    padrao = re.compile(
        r"^\s*(?:" + "|".join(re.escape(e) for e in entradas) + r")\s*=.*$"
    )
    return "\n".join(l for l in codigo.splitlines() if not padrao.match(l))


# ---------------------------------------------------------------------
#  Comparadores
# ---------------------------------------------------------------------


def checa(resultado, esperado):
    """Compara o resultado do aluno com o valor esperado."""
    if isinstance(esperado, bool):
        return resultado is esperado or resultado is bool(esperado)
    if isinstance(esperado, (int, float)):
        return (
            isinstance(resultado, (int, float))
            and not isinstance(resultado, bool)
            and abs(resultado - esperado) < TOLERANCIA
        )
    return resultado == esperado


def _strs(x):
    try:
        return list(map(str, x))
    except TypeError:
        return None


def series_perto(obtido, esperado, tol=TOLERANCIA):
    """Compara duas Series numéricas por índice, com tolerância."""
    pd = _pd()
    try:
        if not isinstance(obtido, pd.Series) or len(obtido) != len(esperado):
            return False
        o = obtido.sort_index()
        e = esperado.sort_index()
        if _strs(o.index) != _strs(e.index):
            return False
        return all(abs(float(a) - float(b)) < tol for a, b in zip(o.values, e.values))
    except Exception:
        return False


def series_int_igual(obtido, esperado):
    """Compara duas Series de contagem (value_counts, groupby().size())."""
    pd = _pd()
    try:
        if not isinstance(obtido, pd.Series) or len(obtido) != len(esperado):
            return False
        o = obtido.sort_index()
        e = esperado.sort_index()
        if _strs(o.index) != _strs(e.index):
            return False
        return all(int(a) == int(b) for a, b in zip(o.values, e.values))
    except Exception:
        return False


def df_igual(obtido, esperado):
    """Confere se o DataFrame do aluno é o resultado esperado do filtro."""
    pd = _pd()
    if not isinstance(obtido, pd.DataFrame):
        return False
    try:
        return obtido.reset_index(drop=True).equals(esperado.reset_index(drop=True))
    except Exception:
        return False


# ---------------------------------------------------------------------
#  Checagens dos exercícios com DataFrame
# ---------------------------------------------------------------------


def _c13_dimensoes(env, df):
    return isinstance(env.get("dimensoes"), tuple) and env["dimensoes"] == df.shape


def _c13_valores(env, df):
    d = env.get("dimensoes")
    return isinstance(d, tuple) and d[0] == df.shape[0] and d[1] == df.shape[1]


def _c14_coluna(env, df):
    r = env.get("escolaridade")
    return hasattr(r, "name") and str(getattr(r, "name", "")) == "GRAU_INSTRUCAO"


def _c14_valores(env, df):
    pd = _pd()
    r = env.get("escolaridade")
    if not isinstance(r, pd.Series):
        return False
    return r.reset_index(drop=True).equals(df["GRAU_INSTRUCAO"].reset_index(drop=True))


def _c15_valores(env, df):
    r = env.get("contagem")
    esperado = df["GRAU_INSTRUCAO"].value_counts()
    return series_int_igual(r, esperado)


def _c15_categorias(env, df):
    r = env.get("contagem")
    try:
        return len(r) == df["GRAU_INSTRUCAO"].nunique()
    except TypeError:
        return False


def _c16_e_df(env, df):
    return isinstance(env.get("df_60mais"), _pd().DataFrame)


def _c16_igual(env, df):
    return df_igual(env.get("df_60mais"), df[df["IDADE"] > 60])


def _c17_igual(env, df):
    return df_igual(env.get("df_filtro"), df.query('PcD == "SIM" and SEXO == "FEMININO"'))


def _c18_indices(env, df):
    r = env.get("resumo")
    return _strs(getattr(r, "index", None)) == _strs(df["IDADE"].describe().index)


def _c18_valores(env, df):
    return series_perto(env.get("resumo"), df["IDADE"].describe())


def _c19_grupos(env, df):
    r = env.get("por_regional")
    try:
        return _strs(r.index) is not None and set(_strs(r.index)) == set(
            _strs(df["REGIONAL"].unique())
        )
    except Exception:
        return False


def _c19_valores(env, df):
    return series_int_igual(env.get("por_regional"), df.groupby("REGIONAL").size())


def _c20_grupos(env, df):
    r = env.get("idade_media_cor")
    try:
        return set(_strs(r.index)) == set(
            _strs(df["COR_RACA"].dropna().unique())
        )
    except Exception:
        return False


def _c20_valores(env, df):
    return series_perto(
        env.get("idade_media_cor"), df.groupby("COR_RACA")["IDADE"].mean()
    )


def _c21_tem_barras(env, df):
    ax = env.get("ax")
    return ax is not None and hasattr(ax, "patches")


def _c21_barras_preenchidas(env, df):
    ax = env.get("ax")
    try:
        return len(ax.patches) > 0
    except Exception:
        return False


# ---------------------------------------------------------------------
#  Definição dos exercícios
#    modo      : "variavel" | "funcao" | "importacao" | "dataframe"
#    saida     : nome da variável-resposta (modos variavel/dataframe)
#    funcao    : nome da função do aluno (modo funcao)
#    entradas  : variáveis que o corretor substitui a cada caso
#    casos     : [(valores_ou_argumentos, esperado)]
#    checagens : [(descricao, funcao(env, df))]
#    requer    : [(regex, mensagem)] — método exigido pelo enunciado
#    proibe    : [(regex, mensagem)] — atalho proibido pelo enunciado
# ---------------------------------------------------------------------

EXERCICIOS = {
    1: {
        "rotulo": "Exercício 1 — idade em meses",
        "modo": "variavel",
        "saida": "idade_em_meses",
        "entradas": ["idade"],
        "casos": [
            ({"idade": 46}, 552),
            ({"idade": 27}, 324),
            ({"idade": 1}, 12),
            ({"idade": 60}, 720),
            ({"idade": 91}, 1092),
        ],
    },
    2: {
        "rotulo": "Exercício 2 — de texto para número",
        "modo": "variavel",
        "saida": "resumo",
        "entradas": ["idade_texto"],
        "casos": [
            ({"idade_texto": "46"}, "Idade: 46 anos"),
            ({"idade_texto": "7"}, "Idade: 7 anos"),
            ({"idade_texto": "91"}, "Idade: 91 anos"),
        ],
    },
    3: {
        "rotulo": "Exercício 3 — comparações e operador lógico",
        "modo": "variavel",
        "saida": "prioridade",
        "entradas": ["idade", "tempo_rua_meses"],
        "casos": [
            ({"idade": 63, "tempo_rua_meses": 14}, True),
            ({"idade": 63, "tempo_rua_meses": 3}, False),
            ({"idade": 59, "tempo_rua_meses": 24}, False),
            ({"idade": 60, "tempo_rua_meses": 6}, True),
            ({"idade": 60, "tempo_rua_meses": 5}, False),
            ({"idade": 30, "tempo_rua_meses": 40}, False),
        ],
    },
    4: {
        "rotulo": "Exercício 4 — limpando texto com métodos de string",
        "modo": "variavel",
        "saida": "nome_limpo",
        "entradas": ["nome_bruto"],
        "casos": [
            ({"nome_bruto": "  maria da silva  "}, "Maria Da Silva"),
            ({"nome_bruto": "JOSÉ  "}, "José"),
            ({"nome_bruto": "  ana "}, "Ana"),
        ],
    },
    5: {
        "rotulo": "Exercício 5 — listas e a média",
        "modo": "variavel",
        "saida": "media",
        "entradas": ["idades"],
        "casos": [
            ({"idades": [46, 27, 12, 63]}, 37.0),
            ({"idades": [1, 2]}, 1.5),
            ({"idades": [60]}, 60.0),
            ({"idades": [10, 20, 30, 40]}, 25.0),
            ({"idades": [33, 34, 35]}, 34.0),
        ],
    },
    6: {
        "rotulo": "Exercício 6 — dicionário de faixas de tempo na rua",
        "modo": "variavel",
        "saida": "meses",
        "entradas": ["faixa"],
        "casos": [
            ({"faixa": "Ate seis meses"}, 3),
            ({"faixa": "Entre seis meses e um ano"}, 9),
            ({"faixa": "Entre um e dois anos"}, 18),
            ({"faixa": "Entre dois e cinco anos"}, 42),
            ({"faixa": "Entre cinco e dez anos"}, 90),
            ({"faixa": "Mais de dez anos"}, 132),
        ],
    },
    7: {
        "rotulo": "Exercício 7 — faixa etária com if / elif / else",
        "modo": "variavel",
        "saida": "faixa_etaria",
        "entradas": ["idade"],
        "casos": [
            ({"idade": 5}, "crianca_adolescente"),
            ({"idade": 17}, "crianca_adolescente"),
            ({"idade": 18}, "adulto"),
            ({"idade": 45}, "adulto"),
            ({"idade": 59}, "adulto"),
            ({"idade": 60}, "idoso"),
            ({"idade": 91}, "idoso"),
        ],
    },
    8: {
        "rotulo": "Exercício 8 — laço for com acumulador",
        "modo": "variavel",
        "saida": "media",
        "entradas": ["idades"],
        "proibe": [
            (r"\bsum\s*\(", "O enunciado pede um laço 'for' somando item por item: não use sum()."),
        ],
        "casos": [
            ({"idades": [46, 27, 12, 63]}, 37.0),
            ({"idades": [1, 2]}, 1.5),
            ({"idades": [60]}, 60.0),
            ({"idades": [33, 34, 35]}, 34.0),
        ],
    },
    9: {
        "rotulo": "Exercício 9 — laço for com if (contagem)",
        "modo": "variavel",
        "saida": "quantos_idosos",
        "entradas": ["idades"],
        "casos": [
            ({"idades": [46, 27, 12, 63]}, 1),
            ({"idades": [60, 61, 59]}, 2),
            ({"idades": [12, 7]}, 0),
            ({"idades": [91, 88, 70, 20]}, 3),
            ({"idades": []}, 0),
        ],
    },
    10: {
        "rotulo": "Exercício 10 — função com def e return",
        "modo": "funcao",
        "funcao": "faixa_etaria",
        "casos": [
            ((5,), "crianca_adolescente"),
            ((17,), "crianca_adolescente"),
            ((18,), "adulto"),
            ((59,), "adulto"),
            ((60,), "idoso"),
            ((91,), "idoso"),
        ],
    },
    11: {
        "rotulo": "Exercício 11 — função com valor padrão",
        "modo": "funcao",
        "funcao": "conta_acima",
        "casos": [
            (([46, 27, 12, 63],), 1),
            (([60, 61, 59],), 2),
            (([46, 27, 12, 63], 30), 2),
            (([12, 7],), 0),
            (([],), 0),
            (([60, 60, 60], 60), 3),
        ],
    },
    12: {
        "rotulo": "Exercício 12 — importar a base com pandas",
        "modo": "importacao",
        "saida": "df_poprua",
        "checagens": [
            ("df_poprua é um DataFrame do pandas", lambda env, df: isinstance(env.get("df_poprua"), _pd().DataFrame)),
            ("o arquivo foi lido por completo (todas as linhas e colunas)", lambda env, df: getattr(env.get("df_poprua"), "shape", None) == df.shape),
            ("as colunas IDADE, SEXO e GRAU_INSTRUCAO estão presentes", lambda env, df: all(c in _strs(getattr(env.get("df_poprua"), "columns", [])) for c in ("IDADE", "SEXO", "GRAU_INSTRUCAO"))),
        ],
    },
    13: {
        "rotulo": "Exercício 13 — dimensões da base",
        "modo": "dataframe",
        "saida": "dimensoes",
        "checagens": [
            ("dimensoes é uma tupla (linhas, colunas)", _c13_dimensoes),
            ("o número de linhas é o da base", _c13_valores),
        ],
    },
    14: {
        "rotulo": "Exercício 14 — selecionar uma coluna (Series)",
        "modo": "dataframe",
        "saida": "escolaridade",
        "checagens": [
            ("escolaridade é a coluna GRAU_INSTRUCAO", _c14_coluna),
            ("a Series inteira confere com a coluna da base", _c14_valores),
        ],
    },
    15: {
        "rotulo": "Exercício 15 — frequências com value_counts",
        "modo": "dataframe",
        "saida": "contagem",
        "checagens": [
            ("contagem traz uma contagem por grau de instrução", _c15_categorias),
            ("as contagens conferem com a base", _c15_valores),
        ],
    },
    16: {
        "rotulo": "Exercício 16 — filtrar por um valor",
        "modo": "dataframe",
        "saida": "df_60mais",
        "checagens": [
            ("df_60mais é um DataFrame", _c16_e_df),
            ("entraram exatamente as pessoas com mais de 60 anos", _c16_igual),
        ],
    },
    17: {
        "rotulo": "Exercício 17 — duas condições com query",
        "modo": "dataframe",
        "saida": "df_filtro",
        "requer": [
            (r"\.query\s*\(", "O enunciado pede o método df.query com duas condições e 'and'."),
        ],
        "checagens": [
            ("df_filtro é um DataFrame", lambda env, df: isinstance(env.get("df_filtro"), _pd().DataFrame)),
            ("entraram exatamente as mulheres com PcD == 'SIM'", _c17_igual),
        ],
    },
    18: {
        "rotulo": "Exercício 18 — resumo estatístico com describe",
        "modo": "dataframe",
        "saida": "resumo",
        "checagens": [
            ("resumo traz count, mean, std, min, 25%, 50%, 75% e max", _c18_indices),
            ("os valores do resumo conferem", _c18_valores),
        ],
    },
    19: {
        "rotulo": "Exercício 19 — groupby().size() por regional",
        "modo": "dataframe",
        "saida": "por_regional",
        "requer": [
            (r"\bgroupby\b", "O enunciado pede groupby na variável REGIONAL."),
        ],
        "checagens": [
            ("um valor para cada regional da base", _c19_grupos),
            ("as contagens por regional conferem", _c19_valores),
        ],
    },
    20: {
        "rotulo": "Exercício 20 — idade média por cor/raça com groupby",
        "modo": "dataframe",
        "saida": "idade_media_cor",
        "requer": [
            (r"\bgroupby\b", "O enunciado pede groupby na variável COR_RACA."),
        ],
        "checagens": [
            ("um valor para cada cor/raça da base", _c20_grupos),
            ("as médias de idade conferem", _c20_valores),
        ],
    },
    21: {
        "rotulo": "Exercício 21 — um primeiro gráfico",
        "modo": "dataframe",
        "saida": "ax",
        "requer": [
            (r"\.plot\b", "O enunciado pede um gráfico feito com o método .plot do pandas."),
        ],
        "checagens": [
            ("ax é o objeto devolvido pelo gráfico", _c21_tem_barras),
            ("o gráfico tem barras desenhadas", _c21_barras_preenchidas),
        ],
    },
}


# ---------------------------------------------------------------------
#  Execução por modo
# ---------------------------------------------------------------------


def rodar_casos(codigo, casos, saida, rotulo, imprimir=True):
    """Modo VARIÁVEL: reexecuta o código por caso, injetando as entradas."""
    ok = 0
    for valores, esperado in casos:
        env = {"__name__": "corrigido"}
        env.update(copy.deepcopy(valores))
        try:
            exec(compile(codigo, rotulo, "exec"), env)
        except Exception as erro:
            if imprimir:
                print(
                    f"  [FALHOU] {rotulo} {valores!r} -> {type(erro).__name__}: {erro}"
                )
            continue
        if saida not in env:
            if imprimir:
                print(
                    f"  [FALHOU] {rotulo} {valores!r} -> a variável '{saida}' não"
                    " ficou definida no seu código"
                )
            continue
        resultado = env[saida]
        if checa(resultado, esperado):
            ok += 1
            if imprimir:
                print(f"  [OK]     {rotulo} {valores!r} -> {resultado!r}")
        elif imprimir:
            print(
                f"  [FALHOU] {rotulo} {valores!r} -> {resultado!r}"
                f"   (esperado {esperado!r})"
            )
    total = len(casos)
    return ok, total, ok / total * 10.0


def _chamada(nome_funcao, argumentos):
    dentro = ", ".join(repr(a) for a in argumentos)
    return f"{nome_funcao}({dentro})"


def rodar_casos_funcao(codigo, nome_funcao, casos, rotulo, imprimir=True):
    """Modo FUNÇÃO: executa a célula uma vez e chama a função por caso."""
    env = {"__name__": "corrigido"}
    try:
        exec(compile(codigo, rotulo, "exec"), env)
    except Exception as erro:
        if imprimir:
            print(f"  [FALHOU] {type(erro).__name__} ao executar a sua célula: {erro}")
        return 0, len(casos), 0.0

    funcao = env.get(nome_funcao)
    if funcao is None or not callable(funcao):
        if imprimir:
            print(f"  [FALHOU] Não encontrei a função {nome_funcao}() na sua célula.")
            print("           Confira o nome na linha 'def' e rode a célula de novo.")
        return 0, len(casos), 0.0

    ok = 0
    for argumentos, esperado in casos:
        chamada = _chamada(nome_funcao, argumentos)
        try:
            resultado = funcao(*argumentos)
        except TypeError as erro:
            if imprimir:
                print(f"  [FALHOU] {chamada} -> TypeError: {erro}")
                if "argument" in str(erro):
                    print("           Confira a linha 'def': o valor padrão é o que")
                    print("           permite chamar a função com um argumento só.")
            continue
        except Exception as erro:
            if imprimir:
                print(f"  [FALHOU] {chamada} -> {type(erro).__name__}: {erro}")
            continue
        if resultado is None:
            if imprimir:
                print(f"  [FALHOU] {chamada} -> devolveu None")
                print("           Use 'return' para devolver o valor (sem 'print').")
            continue
        if checa(resultado, esperado):
            ok += 1
            if imprimir:
                print(f"  [OK]     {chamada} -> {resultado!r}")
        elif imprimir:
            print(f"  [FALHOU] {chamada} -> {resultado!r}   (esperado {esperado!r})")
    total = len(casos)
    return ok, total, ok / total * 10.0


def rodar_checagens(codigo, checagens, rotulo, df, injetar_df=True, imprimir=True):
    """Modos IMPORTAÇÃO e DATAFRAME: executa a célula e roda as checagens."""
    pd = _pd()
    env = {"__name__": "corrigido", "pd": pd, str(rotulo): None}
    if injetar_df and df is not None:
        env["df_poprua"] = df.copy()
    try:
        exec(compile(codigo, str(rotulo), "exec"), env)
    except FileNotFoundError:
        if imprimir:
            print(
                f"  [FALHOU] Não encontrei o arquivo '{ARQUIVO_CSV}' no diretório"
                " do notebook."
            )
            print("           Rode antes a célula de download da Configuração.")
        return 0, len(checagens), 0.0
    except NameError as erro:
        if imprimir:
            print(f"  [FALHOU] NameError: {erro}")
            print("           Se o erro for 'pd', faça 'import pandas as pd'.")
        return 0, len(checagens), 0.0
    except Exception as erro:
        if imprimir:
            print(f"  [FALHOU] {type(erro).__name__} ao executar a sua célula: {erro}")
        return 0, len(checagens), 0.0

    ok = 0
    for desc, fn in checagens:
        try:
            passou = bool(fn(env, df))
        except Exception:
            passou = False
        if passou:
            ok += 1
            if imprimir:
                print(f"  [OK]     {desc}")
        elif imprimir:
            print(f"  [FALHOU] {desc}")
    total = len(checagens)
    return ok, total, ok / total * 10.0


# ---------------------------------------------------------------------
#  avaliar(n) — a função que o aluno chama
# ---------------------------------------------------------------------


def avaliar(n, imprimir=True):
    """Corrige o exercício n (1 a 21) lendo a célula do notebook.

    Devolve (ok, total, pontos) para uso do verificar_preenchimento_questoes();
    imprimir=False suprime a saída detalhada.
    """
    if n not in EXERCICIOS:
        if imprimir:
            print(f"AVISO: exercício desconhecido ({n!r}). Use avaliar(1) até avaliar(21).")
        return None

    cfg = EXERCICIOS[n]
    modo = cfg["modo"]
    rotulo = f"[ex{n}]"

    # 1) localiza o código do aluno no histórico do notebook
    try:
        codigo = pega_codigo_aluno(n)
    except NameError:
        if imprimir:
            print("ERRO: este corretor só funciona dentro do notebook (Jupyter/Colab).")
        return None
    if codigo is None:
        if imprimir:
            print(f"Ainda não encontrei nenhuma célula com o marcador '# EXERCICIO {n}'.")
            print(f"Rode a célula do exercício {n} antes de corrigir.")
        return None

    # 2) tira as linhas de entrada (só nos modos que injetam valores)
    if modo in ("variavel", "funcao"):
        codigo_limpo = prepara_codigo(codigo, cfg.get("entradas", []))
    else:
        codigo_limpo = codigo

    # 3) modelo ainda com '...'? avisa antes de qualquer coisa
    if tem_pontinhos(codigo_limpo):
        if imprimir:
            print("=" * 60)
            print(f"  Corrigindo: {cfg['rotulo']}")
            print("=" * 60)
            print("  Você ainda não completou o modelo: substitua cada '...' pelo")
            print("  que falta, rode a célula e chame o corretor de novo.")
        total = len(cfg.get("casos") or cfg.get("checagens"))
        return (0, total, 0.0)

    # 4) valida a sintaxe
    try:
        compile(codigo_limpo, f"<exercicio {n}>", "exec")
    except SyntaxError as e:
        if imprimir:
            print(f"Erro de SINTAXE na célula do exercício {n} (linha {e.lineno}): {e.msg}")
            print("Confira os dois-pontos no fim de if/for/def e a indentação (4 espaços).")
        return None

    total = len(cfg.get("casos") or cfg.get("checagens"))

    # 5) atalho proibido / método exigido pelo enunciado
    for padrao, mensagem in cfg.get("proibe", []):
        if re.search(padrao, codigo_limpo):
            if imprimir:
                print("=" * 60)
                print(f"  Corrigindo: {cfg['rotulo']}")
                print("=" * 60)
                print(f"  [FALHOU] {mensagem}")
                print("  Refaca, rode a célula e chame o corretor de novo.")
            return (0, total, 0.0)
    for padrao, mensagem in cfg.get("requer", []):
        if not re.search(padrao, codigo_limpo):
            if imprimir:
                print("=" * 60)
                print(f"  Corrigindo: {cfg['rotulo']}")
                print("=" * 60)
                print(f"  [FALHOU] {mensagem}")
                print("  Refaca, rode a célula e chame o corretor de novo.")
            return (0, total, 0.0)

    # 6) carrega a base quando o exercício usa dados
    df = None
    if modo in ("importacao", "dataframe"):
        df = _carregar_df(imprimir)
        if df is None:
            return (0, total, 0.0)

    if imprimir:
        print("=" * 60)
        print(f"  Corrigindo: {cfg['rotulo']}")
        print("=" * 60)

    # 7) roda a correção conforme o modo
    if modo == "variavel":
        ok, total, pontos = rodar_casos(
            codigo_limpo, cfg["casos"], cfg["saida"], rotulo, imprimir
        )
    elif modo == "funcao":
        ok, total, pontos = rodar_casos_funcao(
            codigo_limpo, cfg["funcao"], cfg["casos"], rotulo, imprimir
        )
    elif modo == "importacao":
        ok, total, pontos = rodar_checagens(
            codigo_limpo, cfg["checagens"], rotulo, df, injetar_df=False, imprimir=imprimir
        )
    else:  # dataframe
        ok, total, pontos = rodar_checagens(
            codigo_limpo, cfg["checagens"], rotulo, df, injetar_df=True, imprimir=imprimir
        )

    if imprimir:
        print("-" * 60)
        print(f"  Nota: {pontos:.1f} / 10   ({ok} de {total} {'casos' if modo in ('variavel', 'funcao') else 'checagens'})")
        print("-" * 60)
        if ok == total:
            print("  *** PARABÉNS! Tudo certo neste exercício. ***")
        elif ok == 0:
            print("  Nenhum caso passou. Leia as mensagens [FALHOU] acima com calma.")
        else:
            print("  Quase lá! Veja acima os casos que falharam.")
    return (ok, total, pontos)


# ---------------------------------------------------------------------
#  TESTE DOS TESTES — verificação final
# ---------------------------------------------------------------------


def verificar_preenchimento_questoes(imprimir=True):
    """Confere se todos os exercícios estão completos e o nome foi preenchido."""
    try:
        ip = get_ipython()
        historico = ip.history_manager.input_hist_parsed
    except NameError:
        if imprimir:
            print("ERRO: este corretor só funciona dentro do notebook (Jupyter/Colab).")
        return False, None

    exercicios_ok = True
    resumo = []
    for n in sorted(EXERCICIOS):
        resultado = avaliar(n, imprimir=False)
        if resultado is None:
            exercicios_ok = False
            resumo.append((n, None))
        else:
            ok, total, _ = resultado
            completo = ok == total
            exercicios_ok = exercicios_ok and completo
            resumo.append((n, completo))

    nome = None
    for celula in reversed(historico):
        if celula.split("\n", 1)[0].strip() != "# MEU NOME":
            continue
        m = re.search(r'^\s*meu_nome\s*=\s*["\'](.+?)["\']\s*(?:#.*)?$', celula, re.M)
        if m and m.group(1).strip() and set(m.group(1).strip()) != {"."}:
            nome = m.group(1).strip()
            break

    if imprimir:
        print("=" * 60)
        print(f"  VERIFICAÇÃO FINAL DA ENTREGA — Exercícios 1 a {len(EXERCICIOS)}")
        print("=" * 60)
        for n, completo in resumo:
            if completo is None:
                print(f"  Exercício {n}: PENDENTE  (célula não rodada ou não encontrada)")
            elif completo:
                print(f"  Exercício {n}: COMPLETO")
            else:
                print(f"  Exercício {n}: INCOMPLETO (veja 'avaliar({n})' acima)")
        if nome:
            print(f"  Participante: {nome}")
        else:
            print("  Nome: NÃO PREENCHIDO (rode a célula 'Seu nome' no final)")
        print("-" * 60)
        if exercicios_ok and nome:
            print(f"  *** TUDO CERTO, {nome}! Notebook pronto. ***")
        elif exercicios_ok:
            print("  Exercícios completos, mas falta preencher o seu nome.")
        elif nome:
            print("  Nome ok, mas há exercício(s) incompleto(s).")
        else:
            print("  Faltam exercícios E o nome.")

    return exercicios_ok, nome
