# -*- coding: utf-8 -*-
"""descriptive_stability.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1MHDRqYFobbMr-CuUpFvtxN1u2Z80NCRo

# Preliminaries

## Required modules and functions
"""

from collections import namedtuple
from math import exp
from scipy.optimize import linear_sum_assignment
from itertools import combinations
import numpy as np

"""## Utility functions"""

χ = lambda x, y: 1 if x == y else 0

"""### Aggregation functions"""


def prod(*it):
    """Product of an iterable"""
    p = 1
    for elem in it:
        p *= elem
    return p


def owa(w, *it):
    """Ordered Weighted Average of an iterable"""
    sorted_it = sorted(it)
    r = sum(elem * weight for elem, weight in zip(sorted_it, w))
    # print(f"aggregation of {it} is: {r}")
    return r


avg = lambda *it: owa([1 / len(it)] * len(it), *it)

"""### Set functions"""


def jaccard(s1, s2):
    return len(s1 & s2) / len(s1 | s2)


"""### Fuzzy set functions

#### Membership functions
"""


def trapmf(a, b, c, d):
    return lambda x: \
        (x - a) / (b - a) if a < x < b else \
            1 if b <= x <= c else \
                (x - d) / (c - d) if c < x < d else \
                    0


trimf = lambda a, b, c: trapmf(a, b, b, c)


def singletonmf(v, delta):
    return lambda x: \
        1 if v - delta <= x < v + delta else \
            0


"""#### Fuzzy set manipulation"""

ext_mf = lambda mf, U: (lambda x: 0 if x not in U else mf(x))

σ_count = lambda mf, U: sum(mf(x) for x in U)

"""# FRBS structure"""

FRBS = namedtuple("FRBS", ["DB", "RB"])

LV = namedtuple("LV", ["X", "T", "U", "G", "μ"])
# DB is a dictionary of {X:LV}

Rule = namedtuple("Rule", ["A", "C"])
# RB is a dictionary of {str:Rule}

Consequent = namedtuple('Consequent', ['Y', 'w', 'ctype'])

SoftConstraint = namedtuple("SoftCostraint", ["X", "t"])
# A is a set of SoftConstraint

"""## Examples

### FRBS1
"""

Force = LV(
    X="Force",
    T={"Negative", "Zero", "Positive"},
    U=set(np.linspace(-10, 10, 5)),
    G={},
    μ={
        "Negative": trapmf(-10, -10, -5, 0),
        "Zero": trimf(-5, 0, 5),
        "Positive": trapmf(0, 5, 10, 10)
    }.get
)

Force

μN = Force.μ("Negative")

μN(-2)

Angle = LV(
    X="Angle",
    T={"Negative", "Zero", "Positive"},
    U=set(np.linspace(-90, 90, 15)),
    G={},
    μ={
        "Negative": trapmf(-90, -90, -45, 0),
        "Zero": trimf(-45, 0, 45),
        "Positive": trapmf(0, 45, 90, 90)
    }.get
)

"""# Descriptive Stability

## Common settings
"""

𝒶 = avg  # Aggregation function

σ = jaccard  # Set similarity

"""## Rule Base Similarity

### Rule Similarity

#### Consequent Similarity
"""


def CS(C1, C2):
    """Consequent Similarity"""
    assert C1.ctype == C2.ctype

    if C1.ctype == "classification":
        r = prod(χ(C1.Y, C2.Y), χ(C1.w, C2.w))
    elif C1.ctype == "mamdani":
        r = prod(χ(C1.Y, C2.Y), χ(C1.w, C2.w))
    elif C1.ctype == "tsk0":
        r = prod(χ(C1.Y, C2.Y), exp(-(C1.w - C2.w) ** 2))
    else:
        raise NotImplementedError

    # print(f"CS({C1},{C2})={r}")
    return r


"""#### Antecedent Similarity"""

ASN = lambda A: {SC.X for SC in A}


def AS(A1, A2):
    r = 𝒶(σ(ASN(A1), ASN(A2)), *[χ(SC1.t, SC2.t) for SC1 in A1 for SC2 in A2 if SC1.X == SC2.X])
    # print(f"AS({A1}, {A2})={r}")
    return r


"""#### Rule Similarity"""


def RS(R1, R2):
    r = 𝒶(AS(R1.A, R2.A), CS(R1.C, R2.C))
    # print(f"RS({R1}, {R2})={r}")
    return r


"""### Rule Base Similarity"""


def RBASS(RB1, RB2):
    M = np.array([RS(r1, r2) for r1 in RB1.values() for r2 in RB2.values()]) \
        .reshape(len(RB1), len(RB2))
    row_ind, col_ind = linear_sum_assignment(M, maximize=True)
    r = M[row_ind, col_ind].sum()
    # print(f"RBASS({RB1}, {RB2})={r}")
    return r


def RBS(RB1, RB2):
    r1 = len(RB1)
    r2 = len(RB2)
    r = RBASS(RB1, RB2) / max(r1, r2)
    # print(f"RBS({RB1}, {RB2})={r}")
    return r


"""## Data Base Similarity"""

DBN = lambda DB: {LV.X for LV in DB.values()}

"""### Data Base Interpretation Similarity

#### Interpretation Similarity
"""


def IS(μ1, μ2, U1, U2):
    U_min = U1 & U2
    U_max = U1 | U2
    min_mf = lambda x: min(ext_mf(μ1, U_min)(x), ext_mf(μ2, U_min)(x))
    max_mf = lambda x: max(ext_mf(μ1, U_max)(x), ext_mf(μ2, U_max)(x))
    r = σ_count(min_mf, U_min) / σ_count(max_mf, U_max)
    # print(f"IS({μ1}, {μ2}, {U1}, {U2})={r}")
    return r


"""#### Data Base Interpretation Similarity"""


def DBIS(DB1, DB2):
    r = 𝒶(*[IS(LV1.μ(t), LV2.μ(t), LV1.U, LV2.U)
             for LV1 in DB1.values()
             for LV2 in DB2.values()
             for t in LV1.T & LV2.T
             if LV1.X == LV2.X])
    # print(f"DBIS({DB1}, {DB2})={r}")
    return r


"""### Data Base Term Similarity

#### Term Similarity
"""


def TS(T1, T2):
    r = σ(T1, T2)
    # print(f"TS({T1}, {T2})={r}")
    return r


"""#### Data Base Term Similarity"""


def DBTS(DB1, DB2):
    r = 𝒶(*[
        TS(LV1.T, LV2.T)
        for LV1 in DB1.values()
        for LV2 in DB2.values()
        if LV1.X == LV2.X
    ])
    # print(f"DBTS({DB1}, {DB2})={r}")
    return r


"""### Data Base Name Similarity"""


def DBNS(DB1, DB2):
    r = σ(DBN(DB1), DBN(DB2))
    # print(f"DBNS({DB1}, {DB2}) = {r}")
    return r


"""### Data Base Similarity"""


def DBS(DB1, DB2):
    # print("DEBUG: FORCED DBS=1"); r=1
    # r = DBNS(DB1, DB2) * 𝒶(DBTS(DB1, DB2), DBIS(DB1, DB2)) # aggregation applies to the proportion of LVs in common
    r = 𝒶(DBNS(DB1, DB2), DBTS(DB1, DB2), DBIS(DB1, DB2))  # aggregation applies to the proportion of LVs in common
    # print(f"DBS({DB1}, {DB2}) = {r}")
    return r


"""## FRBS Similarity"""


def KBS(S1, S2):
    r = 𝒶(DBS(S1.DB, S2.DB), RBS(S1.RB, S2.RB))
    # print(f"KBS({S1}, {S2})={r}")
    return r


def DS(*S):
    r = 𝒶(*[KBS(*S_pair) for S_pair in combinations(S, 2)])
    # print(f"DS({S})={r}")
    return r


"""# FML file parsing"""

import xml.etree.ElementTree as ET


def buildfromFML(filename, fsresolution=100):
    xmlns = "{http://www.ieee1855.org}"
    tree = ET.parse(filename)
    FRBS_XML = tree.getroot()
    DB_XML = FRBS_XML[0]
    RB_XML = FRBS_XML[1]

    # processing DB_XML
    DB = {}
    for LV_XML in DB_XML:
        X = LV_XML.attrib['name']
        U_left = float(LV_XML.attrib['domainleft'])
        U_right = float(LV_XML.attrib['domainright'])
        U = set(np.linspace(U_left, U_right, fsresolution))
        delta = (U_right - U_left) / fsresolution
        G = {}
        T = set()
        μ_dict = {}
        for LT_XML in LV_XML:
            t = LT_XML.attrib['name']
            T |= {t}
            MF_XML = LT_XML[0]
            if MF_XML.tag == xmlns + 'trapezoidShape':
                a = float(MF_XML.attrib['param1'])
                b = float(MF_XML.attrib['param2'])
                c = float(MF_XML.attrib['param3'])
                d = float(MF_XML.attrib['param4'])
                mf = trapmf(a, b, c, d)
            elif MF_XML.tag == xmlns + 'triangularShape':
                a = float(MF_XML.attrib['param1'])
                b = float(MF_XML.attrib['param2'])
                c = float(MF_XML.attrib['param3'])
                mf = trimf(a, b, c)
            elif MF_XML.tag == xmlns + 'singletonShape':
                v = float(MF_XML.attrib['param1'])
                mf = singletonmf(v, delta)
            else:
                raise NotImplementedError

            μ_dict[t] = mf
        if len(T) > 0:  # discard LVs without terms
            μ = μ_dict.get
            DB[X] = LV(X, T, U, G, μ)

    # processing RB_XML
    if RB_XML.tag == xmlns + 'mamdaniRuleBase':
        ctype = 'mamdani'
    else:
        raise NotImplementedError

    RB = {}
    for RULE_XML in RB_XML:
        ANT_XML = RULE_XML[0]
        A = set()
        for SC_XML in ANT_XML:
            X = SC_XML[0].text
            t = SC_XML[1].text
            A |= {SoftConstraint(X, t)}

        CONS_XML = RULE_XML[1][0][0]
        Y = CONS_XML[0].text
        w = CONS_XML[1].text
        C = Consequent(Y, w, ctype)

        RB[RULE_XML.attrib['name']] = Rule(A, C)

    return FRBS(DB, RB)


"""## Test"""

path_locale = './'
path_corrado = '/content/drive/MyDrive/DS-experiments/'
path = path_corrado

# frbs1 = buildfromFML(path+'InvertedPendulumMamdani1.xml')
# frbs2 = buildfromFML(path+'InvertedPendulumMamdani1.xml')

# print(DS(frbs1, frbs2))


"""# Experiments"""


def do_experiment(folder, filename_template, it=range(10)):
    try:
        frbss = [buildfromFML(path + folder + '/' + filename_template.format(i)) for i in it]
        ds_global = DS(*frbss)
        ds_matrix = np.array([[DS(fs1, fs2) for fs1 in frbss] for fs2 in frbss])
        return ds_global, ds_matrix, frbss
    except:
        print(f"Failed on: {folder}/{filename_template}")
        raise


"""## Run experiments"""

folders = ["FDT_Beer",
           "beer-guaje-fdtp-s-jfml",
           "BEER-guaje-furia-jfml",
           "PIMA-guaje-furia-jfml",
           "PIMA-guaje-furia-jfml",
           "PIMA-guaje-furia-jfml",
           "WINE-guaje-furia-jfml",
           "WINE-guaje-furia-jfml",
           "WINE-guaje-furia-jfml"]
filename_templates = ["cv{0}-guaje-fdtp.jfml.xml",
                      'cv{0}-guaje-fdtp-s.jfml.xml',
                      'BEER3.txt.aux.train.{0}.arff.FURIA.log.txt.rules.txt.jfml.xml',
                      "cv{0}-guaje-fdtp.jfml.xml",
                      "cv{0}-guaje-fdtp-s.jfml.xml",
                      "PIMA.txt.aux.train.{0}.arff.FURIA.log.txt.rules.txt.jfml.xml",
                      "cv{0}-guaje-fdtp.jfml.xml",
                      "cv{0}-guaje-fdtp-s.jfml.xml",
                      "WINE.txt.aux.train.{0}.arff.FURIA.log.txt.rules.txt.jfml.xml"
                      ]
experiments = {folder + '/' + filename_template: do_experiment(folder, filename_template)
               for folder, filename_template in zip(folders, filename_templates)}

"""## Print results"""

np.set_printoptions(precision=3)
for exp in experiments:
    print("EXPERIMENT: ", exp)
    print("Global DS: ", experiments[exp][0])
    print("Pairwise comparison: ")
    print(experiments[exp][1])
    print()

"""#### cross-comparison"""

ds1 = "FDT_Beer/cv{0}-guaje-fdtp.jfml.xml"
ds2 = "beer-guaje-fdtp-s-jfml/cv{0}-guaje-fdtp-s.jfml.xml"

comparison = np.array([[DS(fs1, fs2) for fs1 in experiments[ds1][2]] for fs2 in experiments[ds2][2]])

print(ds1, "vs.", ds2);
print(comparison)

comparison.mean()

comparison.std()
