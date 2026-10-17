#!/usr/bin/env python3
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Guards the CCI citations in the shipped templates.

eMASS and SCA-V validators flag CCI references they cannot match to the DISA CCI list. Templates must
cite CCIs in the fully qualified ``CCI-000001`` form (never the bare ``(CCIs: 000001)`` form), must
not cite identifiers above CCI-005169 (the highest published CCI in DISA U_CCI_List.xml), must not
cite deprecated CCIs, and must map every Appendix A row to its authoritative DISA Rev. 5 CCIs.
"""

import base64
import json
import os
import re
import unittest
import zlib
from typing import Dict, Iterator, List, Set, Tuple

_TEMPLATES = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "templates"))
_POLICIES = os.path.join(_TEMPLATES, "policies")
_MAX_VALID_CCI = 5169

_BARE_FORM = re.compile(r"\(\s*CCIs?['\u2019]?s?\s*:", re.IGNORECASE)
_CCI = re.compile(r"\bCCI-(\d+)")
_MATRIX_ROW = re.compile(r"^\|\s*([A-Z]{2})-0*(\d{1,3})(?:\(0*(\d{1,3})\))?\s*\|")
_CCI_GROUP = re.compile(r"\(CCI-\d{6}(?:, CCI-\d{6})*\)")

_DISA_CCI_MAP_B64 = (
    "eNpNnU3LZj1u579LrzJwNxzb8rGdXVFk8cAUFFXdqyEMk6R3sxhCNiHku49+f0m+elGiLtnH"
    "75Zkvd3/9ad/+c///a//8e//90//+F9/+vb9z+1P//i/+tf4ml/vV5s2Ae9Xb88C7K/xPg3Q"
    "AQNggAl4AQugesdBewDtn79ou3vbjmjtq3XapUn/n4MJoJsm3AYcB/0BNAD1+gAYgC86X3S+"
    "6HzR1SEDawysMbDGwBoDawysMbBGvc7AOlPpfNH5ovNF54v+5oj/of0PBj3rZ9dPXxpvBuDr"
    "8+5epUOlDIjOugA99lM1TDX2VzNfPAcGYC7jqSpTVQ4FzG+MKBjRtw/ZC5ju7FWgLzpN1Upb"
    "VqaBc3Eantbr9MJpQFq+wxK8tyAaZRg1e/uHF9xgT44Vbgl3+9j62flMHbGar1pmcd/bVHtU"
    "0Qc9J7t6zi3Rkg9O3sxe3pjO0GhO4TQda19Gb5yU3rP+omB8GUvCmenjBSzAjiqbKvtr+nEc"
    "2wATwM7uBfAl6ca33oqDCaAVTm23bOV4K7UPJ87KzP1qDz/sa/Jl1Wlcr/l+zfU1T6HiuzcP"
    "QDN++JEfnMuTC9aYkp+2PvwCOaC8VaMrW1gg7SK1Zi9n7Y5pxaK95/7W/i+1+QLUxgYchvDc"
    "itr7RZc/f4hKrPG17GvNr/VyCbyJ4wvpYAJewAJsgDd2zvNlPmjAiGYgCGvH/4f/3xtpbKjP"
    "AjABL2ABcs0bi77HF50N6MC4t5Ul92PcB2u3fG8dNIB+DoAB6jo/sUZngczmO3M7rNpiNIv7"
    "tuqG517FYf2LlqE9Xs1pYnOS2LjU3OmH0/tyuNmzxw+aAyc762U4L8PhUiwuxYpL8Zckj76Y"
    "TeUvgJH5Fjrg68WMFk0sqiya8D2YPsJsIunVk7+HfvhkIMZr89Hmo02/vlEO6GbTzaabnTPj"
    "EDYno61xNwbXYlDp8GEcyr/G9H1voNWQaoi0z9h/TNZuQwY2V/w4zXDAwI8PZPuSOWiADhgA"
    "A0zAC1iADTjRm5bHbzMMAPoP+W/G3TXu7mRdNvxmBxX8a8yerge0ujMH/6cPVtbI9YLa2N6B"
    "nMKIAPs/P7XeNsPU1fKTqrWB6HBtzmmAwQE9DjqHvHOGOye9U9A5zZ3T3DnNPTufyS/EZH0v"
    "256nSoLPOK1x5AvQ/3KAr8o4oiy1z22/rDQnasN5Nmxut2wsCWULIsDvYEJchd1zqVYxOm91"
    "c0R2MKS/ilC2eUCrjP+dLDtiht63d9047nbgakf/YyvZcj8GWTv7eOv4PPrF9E6OVfSx+al3"
    "gpIYbTtnipu4IPUM5rSnyrNVFnBx4xbL+8e32EZo09Yx9H+UwhOQStrZAg3AEeUMQawadMpv"
    "q+/e4yTDgQEm4M2Wc3v4BI7h18d59a7CGM8BOQU24FDnATQAzb80/9L8S/O+Eg5q9EFw+9Pq"
    "947fjL8n8hXmjWMZP5CaYNCcwMGRGxy5saLOkgTBwRwbwIm1pPFDZUmZt35A2I0DDTMddnl+"
    "C0kCFtGfpI3qvs/4/OgHnBLqf2ALh8FYlmvrnUw7qeZuGGO0HKPOQB8QdqEZqDHQyUgmU//+"
    "LeTUAaPyQfgYu/ON7psmnm06BxBdGCmL7TwewgNL2LCEDUvYsIStezA5rRPCM7lAumneS5dg"
    "5bwMrg8V92+dmfs/78U/7A804BHpmXTw0sGbY8yj2cVv9DukMm709FPpI8sSrf2kfZ/N44fV"
    "AcPSyN8RlaYkOu8UnvK+icw+YP7OKPqrUawo1J4wQh9g97vT4RgbfrJVbz1RT8fCL09f3j2c"
    "fLNssO8H9v3oRkDonsOA1MpifItlWyzbYtkWLS9a3tVyDk8y8vcQHDrCAY1LKoCGwja4hBvp"
    "dsNFdtdPmoc770PL8I4D7zjwjgPvOPCOA+848I4D7zjwjvPs6FFbeJBJEEkWlGnRnWrToCgJ"
    "FVPIpAPap3m1LnaiCiMq+NDWeAsZQrFfuBDIvocoM3iD8ATh8QE95tXBo4MpTqjGgr0sY8Zc"
    "pIfTd24TsW4wEXgILAQOMsTzkE4WZx360qEv/qFGyjrw5DlNjbEObVeLMT1eJTxK9CYRPmbl"
    "fHJArg8DPf2pUotS1prn0un6H71J2v4e/HAMMCO/yucHBAj6I9HhqImolh9OvQC8X18Epy7+"
    "j6EPgVzemf1zUyfrDrtbM1eJ8z0QlJCTONbiE36XHbAAtHuMfo1+6eKoD8vm31xmCVaIJ1pU"
    "FkDU6HtQTJdB4KewS0pyQfNo6/WwXvaSJ+F6exXHuiJb7fxk6xHD7i0GSrOHK35g3Qdh8LwM"
    "jymdN0ewox8efeYH1uq87lhkg9RD0v0EmA7AW73VC8kpL6Qc0a9J9DvvqSoWVe4nOs1W23/0"
    "wxvm3C3uqQt/AOZwEAV0E5cAE4E0HEjDgTQcSMOBNBxIw1nZbUoCFrv8U1TBBkI+xN7nCNPh"
    "ZswDqdSF9S47BMEBjSKIwlMc6Cd9QCTOgdE+MNoHRvvAaB8Y7QOjfWb0CFUwPREd60fCYEFO"
    "5A12A7fx82Nwb5g3vBvWDeeGccO3YdtwbZg2dHfzLEbe6Yi93hHM/IH9a98kxNJvzvy9v2MT"
    "/QDy1IiXhvCxd76e5stpvpq23irT29z8RBqyzWQj3uep0thC32wJx+hrHGS7Q0XemFMgEw2G"
    "CSOk29NYNE7Tw3F6JArwSQ45DvHPIiS2cwpcf6Rk8+OB6Ge+IU5jszA/Prt+6+P5aLVmIUcg"
    "1a0V0gKZv1/9YP8RC56WDeYNns+q39nBLc+2tUbZFpd6+nSn3xl/PPm/+TW79i4nlZd7trd+"
    "R7O8dt7nIqPtGku+pqdT0NlzO7Y0BN0R3pVT8akjjMCyrWWV7MvP9eycmHaqIDod1Vb2N+6H"
    "0Z8fuKlthCds0/8MoK5ysFJV+D5Pp6/Tl3D6fZt+3yb37eHZ8vBseXi2PFz5p+dqlWLDL+S0"
    "XrgYmo36PeO3N2q7cG/gtPQ5p5Zv7jnHRcQsUItMdvH3H39uqdSafv2mXkU//+efQ3fiy+h3"
    "b/q9m071J/qNl/fpO9gan5Dz5wXwa4e8Ywg2DibgBaxoDhLAo5HHHc+vCdnSK/1BTHwQEx/E"
    "RJ4Bg2fA4BkwxKjhvEOcAqF+IGcOyZkI9UNCfV8aga8uIpUhUznogBEj0DF06oioOhAirUtZ"
    "50VcqukXah41RzkSG+Kmf0/rXGIkKUOUckBnO1cqb9302ziRu7sebL9DaoYgoL9FfYv2FuUt"
    "ultUty7uM7lNV1zpl3fPCy18IYYv1PAVORQ9FEEURRRJFE2USPs7RGceWq9TFLSyKGWlk0WQ"
    "9Gq0+dKm2NXvkIHR16KulaJWwuZz1DJdMveXVXoXXbK3L3v7srcve/suGlzZYK7C20f91nl8"
    "nUi/4+JW4HwdRo4cseRFakDTMFA1DHQNA1XzQNU8pGpGszBQLQx0CwPlwkCR4MCHsiD7C369"
    "mmh7i8ahByyUr9MXi8Aa+BJQowOg92i/Flx7ifz4V0dfqVO658qizTFYusHSDW2Og6yv99Xr"
    "6/fCJxvHtnFsG8eWR/7gSe+yKVPg7PKKHzzjB+94W9LvqqFcxLMvoofK8Ik3qFSB3uzyVpc3"
    "inZr6WU7ICdihkM/4TE8SR8RcNj9A79/RIDg+A+6v3h5w5ofPTj/iKO03voRAwqt2R/3UbXe"
    "fJxzjJafg7V4y898laeUKxHoIKwdhDWELwcj6uR5Weet3yJMaKt2PcOXEPnB1g+N65fWAf0V"
    "6iu0Vyivtu8/Kqntd2Bj6Vh+SjujsyZRjqPRJMBJgpMIx+43yWzafW+a+W8v2160sZUwt44M"
    "OVH/OOiAkbVjGvt+HQuEZsibXIGUttUvGU+PLV4FMr/sGtAJpAnTvRY6HrRYHHzj4BsH3zj4"
    "hlrNOP0Osl+r1oRchYzBYJlYW03sKhlR4kvnd8x0yJs9VRp70WtUwR+QurbYoeOmED1+vPrh"
    "6+VjQmJwQpzVUmLYHMCmp7mQMS40CutkG9rskT2mBOBc+2tbVtABcFYLp3VG+4WSAR1DR0/a"
    "EZUdqO8FUNt6YcP+H+SNB479wLERT7mexvV0QLc/4nqhsUBhgb4CdQXaCpQV0gpiYXI+QGNQ"
    "4vZK2n8BNAZpQX1maCsNJZqhRXMwogMdLr8RNEEL3gzPc8m0L4NFf7B5GPHu77z7O+/+zrvf"
    "ULk5oM/4SZ8wvgbjazA+f95GTzpzPjw62Boc7KtJF0tx7st76ncsuJQUP+4V3ugytvQJjtTp"
    "9HExLAaEHmKrf9hX2L6olt86zUS76YTuFsS5kqQ8mCTcNOxjKo5j5gPdkpZRh+ydI9SB8342"
    "qpHNlm+pxn9ctcx27kXBhgs3hOMW/3urWszxrPod4xS11e8Ynp+a8+Q6cLKPjgxHKz79+U86"
    "KChC0IOgBkELcpwGoeQ4TmcONiMQHYz1DuAmd24y1iZDIWfSyKF+M+nfsJoZijYHJ3rixByn"
    "V+gcUDmgcfDFQ8WC6jH0JdRLY4kIkX6HtQUbUyg6HMmhOC59olI4zm+Pk4vj1OF01VKjKG7i"
    "I0aPsoQvOvqIjj6i83Hn687nhj7QuiyDMJMuIZW+ckBSSva3kDGqrmZXIbUPodDQb4vf7euM"
    "GnmcDVQaPZvMBTKhGTWPwjNyPabQ2YN20Unc8bGip+j86PxykB8kpTqWPW798G112fYY1SfT"
    "m0x0Vp38BmVpnznxI0zWSNH9OCE5In8cHlnOnKQcJynONP0fx2PmGpWN8rw5Mmnlg3HyS5v4"
    "Vlu1opAQ9BkdfUYPfQblWh6/xWgMUBicZVWS3UhYn7d+Wek4jmLoYLWaftvRLIRiAayW1fnK"
    "8Vse5sjb+FKRny6/yGGVVDcQzX5noiV28TfMOqvmrwU8opihrUD1gOYBxQN6B9QO7ZEpULZA"
    "6DpvFOtoITov244WAv29Azp+VMrtQlTsupTS7fz4maZAWRNlTpTa4sd9Pjc0C02aha7b9eNn"
    "mvqajJGMABeLeMP/iDe6/5qg6BaRQ3aAjsjRETl6yz5kN+Et2HgLNt6CDhiF7hZiRNeLl7pp"
    "W3p6juKNX2iyl4Cf0rlzVm+NXhSniQrdomxoyIrKsH99S/sqDzskxYak2JAUG5JiQ1JsSIoO"
    "sAVz3oZeCqw0TxvjbWM8bozXjeGYYjimGC8T42livE0cZI+x8M7KG69I48FiPEocvFEj1hnr"
    "G2/Fxlux8VZsvBUbb8XG46EPGdX1XGn0ynTxOjG8TgyvE4uXya80VfHCbLwwGy/Mxguzodtt"
    "PDMbz8zGM9NbF8B2ojcP9Brq6yCHWPYp3qIOrLCWWAz9sPGxZhXNLNITkCv73LbeLGISol6/"
    "rjWq6dHKo9sBV/D399yzxTQwvj2LaaDufDC4PVgWBkcDpaoh1RhijSHXGIKNIdkYoo2DDTho"
    "q6jMc1NCDqZOBxY9xp5JIvj9cdl59Mr+/b1s4Fl53OJZiFyseDtdfxpH5Izi8sQT+nvulbwM"
    "Qo/GaEXbKKzWEQbGvtjs4mSfK36xMkcmLDW0szCvQtObQwhLhB8wuRjIvyBcBSAEWPi9EQ2E"
    "xULSczGpvp75tYp6YWMDeXe0MPQ3q6LwzWl4ZBmClYN5y3JwmPxbfy46hwhLtmdddPbdx8W8"
    "ifn0thLz6SPH1nNHwlAs630b+V1YimW4lxpi19peg3C7J1Jb1riospaH55QKquocF5Pz4x7y"
    "ZO42cyHFWxoiuuMM4LuGJcqwRDmoNt7b6gZdA16Bw1zJCT9PDU8Wdp7iTXZ0GdLDSK7Sag1D"
    "OcqWbjGEfSv0rMBRkD5sy4D+qZBzwjry8iixefuus4XDhkzsvA66vbmzPZaetzQSfUPR46V1"
    "13T1ZGBvdd36CFxdzrpwrS5cHzUerO1tq9WqHX4n+Fy47A6gaZwK3lqQHrvJBbM64z22po7A"
    "yCp5fHqs/JGjSi5Kj0XnNWZ1J7rcGWDY3XbNv5wW4N4N7u1l2etotywP/NDwMcC3Li9HblfY"
    "1FVa9XGqCX4b6J5oP26hyEYFGqhFzQ3AxyacbGgZ1tzlDYPY++oYYsvAvuWAAwYDQ1Q0ZEWT"
    "RHiQFSU1HojukYOddxa+NXKqwdKD6b5hu288ExrPhI7KsMNZO5y1w1k7nNVBjrj8H3k8NLnc"
    "vdLCe5HOBBJ5wz7fZKCXTx2Olx3HS8MGZtjADJnRwZuf5gntdgoRJAS5t6EU62glevhsenns"
    "AXy4c4llbe8wUxnY4Z5dDFos9EVyEMdD89lfHu8vRv4XK/87NZyc390nmFFY2YSdiaUlrkee"
    "5j9KuehFDIHr2XU99aJV+YlyLh82epNIGmKnylseGJxbUH3299Nty9Hg9CL19tm33aTSKLwd"
    "4BrwnluW4w2GKUwuKMrEE6db6Bz9zunM+MWaYr9G79zQOzcZ8tE2OmD+pz6o8y7rUBCIP0JE"
    "7Nxf0aKXV+yLguQ98l/wthYKksVFXCKtKDgR3Q2/QkOANyR4Q1I3+RUirzvIKZWgid3fQm4X"
    "NlcFo6KUxkfmqiAbf5SGpw313kZhR2JzYfathvvok10Gj5J35rKcf/AoXB4brgC+SbkJ4dQ0"
    "9G5eu0wegUNJ9NIKKh2UqQ7GtYqkuxrEIJwzNcLcQPkWjN5v7Rw5pqewQAbaEo1XHzcdfwAH"
    "x2u1cvg8VUv+c3KgCw86XOiGnALxmeNK0YaDcth6qlt7LibbggCgl2joIdopz75TK4pUPexi"
    "s50pN7y3sNmW/N7CDVleYNlEubr2vHsDCXrAXE0u7LgivOVsLVIx5CLb5By2AR9P5OwKtjjW"
    "9YzOCzS4lJKj4Q0OrPyAcyhwtgErG7Cyca6fcM4LtjbwlRvl5fsmabNerr0lSxhUXi480IIu"
    "Zx0u/VhyFsX7Y13X3zr+Bl3k+g+sCSOsCVFhZgWmLidvjBkLA8fCwLHKYz2EE5M3pMkpuVyJ"
    "Sy7Biu7ALjqdGu22UJ3N9DWMk27aE2nhm1wF8ZPAurEHDkT38BTTtDe7CKEDy3jDNN6wjTvA"
    "MYa3hulC4ftaH+LjJ0O5ybFqPuUHmYt9WvmaFELahN/BgicP8CmHXgTuyfGdHF+ZlLEiO8D6"
    "h7fN0+Q+IIATAX4IE94s2/bkXUp7RntGe0Z7FtZq71FTm4qOQCafOpUSFLxwRCGDQCyYiAWz"
    "5VhrtmF4FqInogXC4hdtIzdgjG5YoxuG58Fbf/DWH2H39Q9mfEBXnJPJOZmcE97vg5f6wLLj"
    "ID94w82UHgLPJFEwMA/DyG4M3xi+hdWcr2qgWHGxSjvIohV4+uXVjwV6PAHo3NQ061x+6nVd"
    "sBt3BKWOoNS7wjtw+Xr1ytPpyF7hzViSG6ZkPx2t3HeyXE4vyOXrw9aTMLzSoX9Pd0YXnHGS"
    "Yb24Qw7w8YF8LsjnYl0W5BOlfwsjkr69DqzyK5vlV7YSS3toPxbrgPmnhWlH3llxtZbJ+dUK"
    "+yYWVx27nlRZF8lIfvBoHJ3+POUK1bOcDqGawa60FjHfRbgLjukNx/SGY3pb66lK2T4+ukve"
    "uNzOxe1c6/oy5az2LMROhDyFrmvTSSw97BxGsFMMJQ1DW8PS1jC1NWxtLRzFNdNY0C2fuPA9"
    "2+WYVkV8hZE5tLNODnQ9NhxgFwe6teFAu8jXbR59D7qLhu7CwazyDPKBwMkwc55VJCc/5YmH"
    "KWSE7U1FM4uY1Hs/WIllXO/16I5FC9OIECcR5c4dv1gkeUBDGDGLNLwz/d3FyCCLGEQG1r2B"
    "eW/gdTnC6xKagC1uYIwbYXcT+81h4ga2P0z5TSz9nI8kkK7Q6EV5KTvot6xnGRZZ9hTDRQu9"
    "U3D0YCTYLRrmhoa9oWFw6PLw2KOYf91ljAQtHB7FOQInbsK88PzDSudgXeaSneCZua2+fANH"
    "d1DJ08tjvTYwrAeByb6595gBWpgBZJmObQp9fpiun8TQNI8gnmst3BGjQrbGsYrXWaBzmDxo"
    "UNM7WGXYzhHJK/692DiDPKUa6veGNr6F398fYTbzBzHbgnCDJr6him/47jmYZQHPYDQUjY/V"
    "x7nbaN8dXL/3rHs+jvBPuKzLEU/yU6B7otnJZ170SPQL+rrBB611TDabcocjcJptT2FnussT"
    "bwOTeXY2cQIPcYchPD0HEj7ocLCOb4KDHEo4oOOl4KCORKtuTedvFhfJQSvCKMIi/nL9vJ+P"
    "43dWQ/WKkrU/YjbhBfit3hg9dJDfw7OgS8koTWIoDr//3eRPVayueEA9J9tLpUVvCrSpuidQ"
    "RFPylkeT2IlW6k1hNwcHV/l343OE1XLscwMfIxoBM7+Di92JJX4QboJvzXgVuYYEgG56oJse"
    "oZvWNye+wdLVrN04yxwxj/LGGje7veSBaQpEVdQorvjNblRlxSPwekfFN0JRreDIkNYdzXhw"
    "f8F/abwVblc72BSFiF4P1V+X6k+6PrR4XWo7VHQdb5kub5lHzkwVHJk3rqPC66jwOpb4IYe0"
    "V0uDozPaBwc3cnPlN3SGJkMhRYSyOLCqlIu8FFfKYNapolxLXPYbmnVUcZ1glx4KuFiBJ2sx"
    "L/jsa+O+ZbKItrGJoY7r6N98hW5MZ/ZyFE2qqM59v4+t6TyZI1Yl0CvRPECeddHREroxb/+9"
    "sapPohHVGs+bdkNNessyWkJB1tttrmfnFRk44xdRKQrv3Td8NPYmwlOEmImgwb4Km6PuEh5p"
    "BsVXr+DWZLsdW7mDUdic1Li95YL3uicpS3bFqihYRdEq3e6LMMeHTbfPeoJnRA1D5CBKfaUA"
    "ERRQDmgC/UDnyEn9pMgQtE1d8SAKCCEipCsIBA3TQN0yULcM1C0DdctA3TJQtwzULQ54TRJT"
    "sSAMi5iKRUwFPm1jKZSwyWG+3fdkXCJcHruCSBRFojASXB47qqXeFXXY9BylITjz6np3fhrK"
    "lSBERDEiXYG4nEq0SF6VASKrLGSVhayy+uddG2SqY70lrMQBHUNDFQOiIBCiQBwwBL16FZeo"
    "iFFoFmK4A9oldGEVJWn3eGjJKo641amQ1ojAka7IEaT1QYiHg8/sTlbFeqQFtr976D9ZiHkO"
    "XcWQWUfLTfjCMn3AwOy9YbnZYtfbvN8ntyXarjpnJoawXo71qGPdU0zrEeGJm+Ca65aNLNsX"
    "k21zmG/wWG95xoe0BDUtGQP6kLFSNlo0rYR79Qj3+pYq/47qp49L0YswofvpqHocYFO92p0K"
    "cCcoxAGLUhRdBgLH0Qn3ZkhHdcOtFQ+EQshBbUwFag2u03jHRWcnHxNqbZKkmV/XYccRpeQv"
    "xLUS1HqVgfIOfcuGaGUjrO9kG2VtCY0aJ5sRMRgc6SHb47n2sziVg3jDva6dLc9FmBcVIvex"
    "1cVkTYYOJAF7Pua5nmUYOqDe9ry37GTZBn0KndTbmoLwrtUxCTdhKR3tWrd2DXxJuK3dtvtI"
    "TFpSdvxKa01JOYryD+WYsNlFb4XIVjAqWK+mcgOkQrOyMl6BjtAW2zKenlUmxChgntwXlGMO"
    "WK6hCEOaRxIynJ4MQZHolU74SjcFJCoiUSGJ1q9dMicREYp8bh+bZY5csYYKNsRws8tcJZVZ"
    "JzClm+w4tZtt1uymLIPj2vUyKcRbJrKnug8LXhncWuCYB3zD4BtWpuh+c0u8MpSVUeyuPJIK"
    "SriOEq5HhEpUyM4QWgyuYCsPzJDYjT6uSx9HkIqDMobdYcIBFKFiZcgcRYyM60HIiYN+y3Id"
    "uB1Wt8PROQGZPaH+Vrs8YurckND4hUkvQzSh5vP5WPpGovHrqesyeuAM3ATk/GeLAjxgeKag"
    "JexoCR3UgHWh0Y51tGMd7VifdSHGW6Gj+L2h6esouvrEgYR3sIOaooI3Fb2Ccq+j3HNwS6uh"
    "QNMJQs+s2zF2lNJDr1XQSyHCTvSz2hjtYnKZhmJhcz3sCRzT4WbM8VbBbYHpjH3R1Qxzs+ei"
    "c7WtXYwlhv6s+otl5iqRqcZB9Rcbwz2aitrl4kx4CVEmPcNMqHcjdFm+8guwG6irMF9YzJx5"
    "QC1CdRHDJkxkIobNV+5eNSyLIF8+e2f5N2VH3C9pGsmT0MmT0AlCcdCrZhB0QlIcWGF3Ypkn"
    "XuQR5/4jgplcNqQNLtXkUhFN6yA7L/lz7vTSqvs79ypE1sCMhvXXwa6i3Ixyfyt6Ok+OTSfo"
    "RdWNxtXQuFpX0CB23S6vsTLOZuxaxwmr44TVccLqOGF1IkQclEk6ZTm8rzoxIZ0UPg7KpJwr"
    "Iv/nFzL9ykw9WpUnr+YR2uWe+somDZHmReYS88deGjV5+b3zWl9HYulWvhx415yP9daynLY4"
    "CziidMXDnDDm6n9c1vVRHeegIoab8eAJjSrF8GS0cGWMqjlBzkgYf9fHZHuyjCWDAL9rXit1"
    "dsEpedfHeF2B4swfGf392IuTIb+copdT9HKK3n2HnfwZHboDGt6fhnMdkFzeMAWXZTLizwd2"
    "XFlasd6edc2WkY8I0skjo/PI6DwyOo+MvmRM5Xis1uubOD5L5tR2DbdvYmmEU7LqlJR4xGOj"
    "r4/FNJZ2dcXFY2OFPK5uVX6ynKHV2S3HqI6Ov6Pj72Eni7JYQh4SDq7xOFUTa9ymUyHBA6Gv"
    "OoI7IvAZjpO4iSepg2txzkasDMFFT3kOOGDaELsFsVvlKFE61r4UkgCJIxOOg08z2XD5gZSp"
    "tkeOnMDkeKGcGAd6pMqhTISOJDYd00DHNOCgHFjqWmEncFCjkni+lJVg5QRbHBQO81IagjUr"
    "IiVnsG8cSG717oXIreRkYkVwcGNNchc5mGFFiLCU3MXzVOxHrgKhZm1m+Ip44FbAKWcTO0PH"
    "ztAJ6ulE9XTCevpW5A7OK+3NUKDijpvzuCvkJu2+HbND3xVeU2//jWgb6VhYkDdwePlXGGZa"
    "hByxCrETodDoG7kaK4RB1cGuUNHYxc0x2Z8IzRwS/HHPp7DZESdmz4z4DK0o9g4HOaQQlPHa"
    "7HhtOsihhbyK/2bHf9Of8xm8UJwVC0jfilUhjg2VlZGgxcJN7MdVYfv7f1QsRqaSgLdttnvv"
    "t4pyzqgIyBFk7dyvcjIVCjJrJapGseatCPOjnBQVapGjxXbR8fLr4eWnopFFCupYFeKQWFhZ"
    "iGjy489mkF7Q/Xd0/12uWpFKTJXyU24zvlsd360u360uMJ+qGSuDR5eDVm79LbG0P8vrvQVu"
    "Xkf+HArbhbN/P9ejvt8WWIP3ue78iZYpC0kHVy0HdivkeMLhn4+VGWlVsEDlKBEv7IoswIWq"
    "VzSBnAy9lC8jjxg97co1Fhk8Tqa5iaOF372/vqqKBU7JZohdVQ4PJfFQFg8UWpgbHBDAi0IL"
    "D/qBB/3AkGAkmDCUCYYywdAeGNoDQ3vggCqMOXQGdKnkFfjbjyfM/2TVeQVo6s1kUbrJIxzx"
    "ZZXPHCIov4i6dlD2+cwn8WB1e/oubGYlIeT0IV4nnhAynGdbCnoe6QiwI0WJYpmZLK6AvA4c"
    "9IgOjhqka3hI1/Ao7hlfEhy2Bw7bDhSRTJeKXSa0H1WaoUqzHjHFBBKwDajSDK2Yv5Of7KLm"
    "QtaMByMjSW2Gkto82OGfrThjFhjrECozQy1mqMUcsAe4R4xnVYu5Dvh9oRlzcDKGV/ij0GKa"
    "RsOJPWTgXO2AQFekU+QWwzfWEFUMUcXftRQoIlmBxkwPtzQHb0UIR8cYTgaGk4HhZGA4GTKc"
    "tOfWnFmTHjkZraJ+Ky9iC0HmW/GmkV7X3z4ZESPq02d84hcBu5JmfkXo18D1epBubeBt7SCb"
    "TAIwsKwM0ug5uEU5B1NSGivsSCyzwDCKcWVgXDFSwhmM0wHBxhVAnuxqkHpsYG9x0Koop48t"
    "TOaWNj9RxNlVRYeXoDGwfQxcl0d7PyHG2dJ7Liaz7KwKZG/xk1lykrGZDIIRB8GIg2DEgcVk"
    "KBiR0Esj9NL2cxuo5eKUt/1B51JxcsWbCNQ0fDaMQE1ToCZygSEXGHKBg30/z4ly3GFoA7PL"
    "UKTjlgc+gSe7zoXXz2UgTQwWGAfnluUyYJnDE9oka+w2boVclfPBZDpOhX2fedF5/LgawaxA"
    "i4QR9DcI+hv47Q78dgdBf4Ogv4HJYmCyGJgsBvF0AxfegQvvwIV3kB/LtmIF8OtBvDHCig2R"
    "xhRMvOuMFisYJNQaZNQa8LYRvC0qZJoizHhd4SHw85CCosLICkqJxD50gfdWmJnoiLGucdFv"
    "oj8trcQwC06MfOUwYgyMGEN5G3CCMEUkb0ImIy9efJ65Tjkp6U0bM3wSr+pMf/xdYc4furMr"
    "C0EwCawWQ6SWoGUHNaMVpaw6+wr5HZDfIfKrQGY85wzPOSO3iEVuEX1bC36U88lnhaHCSBVi"
    "pApxYLdqZm2C0in1lWwUEOMBMR5BjKNqJY3aoGm1KX8UX+KRqPRXyn+Fl+tQFizSeA7lwlIy"
    "rPRf/XazkA6sGEMpr5TzSkmvlPUKV9WhzFVKXYURY0TCKmw3Sk417lrmG3HgpToiBZVyUHGm"
    "SXvn4NyqcSaUhEpZqEaRzJYvx4HxYig7VWSvI7VFVwHnCydQB7lT0qYOpYpSrihU/IMEUQ7q"
    "2yeqMKL9MVLHJuGN7uCalONNOZSU4+XGvNyY1679N16XA7f18crwDfF9580ZHN4TA0f2gXpj"
    "hHojzKf5sZJnvdek2/MT0k2Eq3qgY1VfGRE/zrD9TfQ1KfeVmI8NdyfmZv/tJzHK3XUNuuNJ"
    "9B3MyIVZ1yl35JpsWXgZDCv97lG21pzVVkqwXdicFJlNXpm3j4yh/Zp68jNlQT6fJLp5mXle"
    "D57XY10jVbGp8JOT30c0suSYu97CWmJporxTe3287sexksoKtmQ9koNJVjtKniovkxFFb+Ax"
    "1ymBbbldlYgJsxjBLOSVNhOLr0e7jluxWUGJwu3KEiOn3Pe6WFWyM7xErF909mWZozB9D0cE"
    "5wmRPcjbrbIWVt61cFj7fl9aIwLU5BKT41DeNbmp7VFFORWlSIS97vKbqQu9I+vaLieZHCW7"
    "H8lL5SYZIyNkfBwlFeurinYW4SHYrxtkNM6TbJx5/R6zGa4foTWDF9iIF5jKsy1u35lvYU9i"
    "cU9UBj+lnXuVEq6Vw2Plvd7PxYzEVJ0eP+kXanOU303ZDeVSuVfVyyUncGIQODFOrYSeVP6z"
    "mrT4SZNnVDauyDmGf5WFf1VbpS7YUQQbfrCmPaWhkIuVEQ7s4JMAKhKUPeMp97Zs225Kl6xh"
    "cjsjUYzt8j3LzuZTiJMInMzmdTJbgS2Ht1nViI181k2q2rLrNS4m+ybukVeRPXJ+Wx+HtGz6"
    "4/jWckykvNB7iWePRUTqH9dHy3gCWQSiCmuJpY/9Fja7R/QmD5MpD9NzcsTabiMzkikzEs8e"
    "49ljPHscrKpXWQPLHa/sjxZeYoHJBIFIBLxvjPeNg3ErZHpAKTnKVa/VhsXLJzBvYpTaZlfm"
    "mWy/7VLnJQLJsCnNDMaC0NhgLGhKFsMZItmSNSWC+eR8iZVXivBmVwEYzNN43Fg8bgKd6RFt"
    "Xkz2zrGKlNmBzknazUSTp4JHjrWZasIUXQ0HM+ORYzxyLB45JIOpcvQEuIk56KXLygb3LkSu"
    "V6USUcb6dpS4BP3IcxNPxJy7WSF2IqQ8ygQFKTU7YlUaiJgrUrL1q/6pxItdCcoqY4PEFutK"
    "V4A1or+pEpKgY3gQWV85Irl0mKLV+kqNQtzz0fL13yKfY0tVydQvthLBzUYk1bh+2oYQZwhx"
    "RnSRg1SdrCpXSngrXc97k0dWMuFI98/wSQRqBPSYEgEQg++gVDY70kzSEZooYnccoGrgig9s"
    "MISmO+BbLjKinCHKGaKcIcqZwr4R4GxIfyGFRGRe+xGZImwo1T1aBTw2HFS++1gn7qxivhWz"
    "Lc+NcXZVqekd5cEkESY3E0cNC0cNammF8dIwvDSMPxVhBDiZ0oQqTygOGWa1CbGVShSqTKG4"
    "ZJhSg5Ib1PhrDQ74tuVUYqNxuXDACHrugDx2TGlBredeyenGCDgyOVQY1xcPCsODwvCgMDwo"
    "DA8Kw4PCQX37RjJOviXljDKBKhVo5AJVMlDOgPFoyaydjL6ySSvA1yKFp3J4Koknl1fOEsaF"
    "xT/Cwj+CL3QUCOM2hXErIlv5PpXwUxk/lfLTSt+n4GBT+k/l/1QCUKsjKKcGUzJQPCiMlKCG"
    "04Qps6dSe1r98YQRm8cRVG5PJfckgMlwlzDcJRzwLUdQaT5xlzCl9MRdwpTBUyk88ZBwwBcw"
    "C+XhNA6esnHiDGHKyWmnRhrngIMXnhBSSgYFxFfB8FVwkEpJzRrfAQuXgp/xRw8MTwLDk8CU"
    "shL/ASNAyKZUlOw0vgFGIJDhEWBT0UDsL04AljE+8VcPTEkoifExYnwMM7+Fmf/n/aMGhqHf"
    "MPRbGPp/Xk9rw9RvkXjyZ/zVA5vK4sr+Y9x3QJMQbOz5DmhGSV4jz8yNF7OplK+RdPLGCfkB"
    "eQJh8YsmRd5B1ZccjPlaYetLuuJoYPx3sKt8ZDkDXdm87hEeAUZeSsMLwMhMaVj+Dcu/heWf"
    "utUvJ2auU9jsd2eTb/yiSY4RDgIOcpRFTUmIbeSltnAKUFE1RPMcr8nxmpGj8i/Bs4iPsvAN"
    "AFWtceaUenKet4qytZPN7/il/LpK2oImFlIXyWp/ffsky22ZdqS2SAHjykX3cgTffst7lu9C"
    "jETQgxjPr2taMrzVDW91eyvjTCloLJwDfiVnxm/biBo3osYdpEPgjkIGAvV5LQdyAo+WmWP4"
    "zmwsGCUvdeOl7oDWSk16p7dOIXI+W+prvmIH47H7+++mB1F4S8VQBwsvX8PL1/DyNbx8DS9f"
    "B1cLnbPFRu/go4uurMQklXyUzjJVPyXlrHYRWbcpieUpbOYvhn2Ef+/vj8yLyd3BKOxMLJkn"
    "+yzsm1i677e3lVh667e3ndmS6W3c3k5i6W3c3uJJbzj62hq3u1oKZe8cn+nm9OBHa9wOU5bE"
    "w9eW3R5TlsSIb2muFzpnCAVb9ukyp8jZWfbpMucoRbx9usxJQtPW/HSZs+Q8pWlfu5KznMoe"
    "fbvsOUtIX7j5BjpnCe3LMHWhc5awwvXeLnvOEm6Y0elC5yyVQfT9dJmzhASmd4DQOUslP30/"
    "XeYslRF7fbrMWUIU17pdjpylcmSv2+XIWUIuI/gw0DlL2QTW56jmLLlloXmROSOHfS4iB3yu"
    "VSWHetXvz63CvYHHrqtsb3kaSeLpYH40wplOe3z0sNEuAWu2pV23j+I1W5F7aJ2Nnmm9lVGp"
    "HD4rTff7cbuNbVPiRkICTZkSCQm0va97cO7iVnpxGUD2dQ/OrUTz4uDT8Eo0DSOR7H2TGeV+"
    "bmnDz6eXnMdR7p7r0Zt9I7fscuK8r8tdbpoVdefizryYkRjl1sGd6rm5XqqsyXuynBiLvZyP"
    "T2Y1i1x82vUmTLJFfKGRhNDBuWUx5CPPzPJEthm4cigsTk1MoR2lO4F7oXWyU66YVpwbtZOd"
    "8sY08e9T3pi24mf1tOMnrmbIWgeqdkZ5Kxa5Jh2hEQvrgMYrN5KJU5F20E55W84ncErnPsob"
    "L4empEfKX4S0fOQWh7Qc/gKqmYuFiHTe67GWx+rs68qVZA6zvYOP09KbGeLLS6lXind/7swI"
    "GAx0pZJ/Qa+LzoTvz/VSqoqtkeEC9yryvhO/NZ/yIWs3CX2juVbN7cCR6oO07k+5kFX+g0lQ"
    "4Xxu0o3K2f70cTGV3d4uJlPb93kxMzF07hL1DAcAyk4U0PnAK2zQ36j+Kjn7Uy5nrVKzP+Vy"
    "1k6NYMyLyRGM92JyBGNdTG7EuCMJ8jbD1yAwO5P01+4/8ZMxWo5Rj9VJtP7EL2GGno+CHgXM"
    "mcTxj/4gX7mviahN8utNlHuTGMtJfr1JprwZwZW/I/HyJGXeJGXeJGXeJGXeJGXeJGXeJDP7"
    "JBveJDP75M8tTWIxJ7GYk1jMSXr1iXZwhnbwd6RdnvhJTPwkJhrBiUbQwZs17h8foJlFM8FV"
    "IsHyRBk4UQZOfCAmCsCJD8RE6TfxgZj4QEy0fRNt38w0czcX8yRbuoNe2NzbQ0tBIK9abWZ+"
    "ucjZPFEITvwgJn4QM9R+v29e5onWb2aSuZuYeaIBnKEB/H2TMk8UgBNvh0nWuRl/X+73Tcs8"
    "yUA38XuYTX9WoWWrU4VcudayyVnd6+8u8IcXwuNBRTmGls2/8Yu2W46+/t4DKkQH2U/8QQf+"
    "zEKmmovczBOl4szMcuHSNzOr3K/7Zw1az97iLzaic5wkeJ/kuXaQXcSfbiTj9SQT3SQUdpJ/"
    "bkbGa1WpJvnbCpHZOtA5r0GrRqt2W60Vxu2zWQ5eat5JHOzEO8PBJ9686p9SPVSnpai8f7ui"
    "4sel35+Z6/rbNebMVn/QrCLoHbMuJvvhOhH+OtFrTvSak/DXicvjJNB1Eug68eOY+HFMUtBN"
    "XDf+++tP//a3//fvf/vX//Mff/u3sELqLdL/+b//P1dPtoU="
)


def _load_disa_cci_map() -> Tuple[Dict[str, Set[str]], Set[str]]:
    """Decode the embedded DISA U_CCI_List.xml (2025-01-23) Rev. 5 CCI map."""
    decoded = json.loads(zlib.decompress(base64.b64decode(_DISA_CCI_MAP_B64)).decode("utf-8"))
    by_ctrl = {
        ctrl: {f"CCI-{num:06d}" for num in nums}
        for ctrl, nums in decoded["by_ctrl"].items()
    }
    deprecated = {f"CCI-{num:06d}" for num in decoded["deprecated"]}
    return by_ctrl, deprecated


def _template_files() -> Iterator[str]:
    for root, _dirs, files in os.walk(_TEMPLATES):
        for name in sorted(files):
            if name.endswith((".md", ".yaml", ".yml")):
                yield os.path.join(root, name)


def _lines(path: str) -> Iterator[Tuple[int, str]]:
    with open(path, encoding="utf-8") as handle:
        for lineno, line in enumerate(handle, 1):
            yield lineno, line


def _where(path: str, lineno: int) -> str:
    return f"{os.path.relpath(path, _TEMPLATES)}:{lineno}"


def _norm_ctrl(fam: str, num: str, enh: str) -> str:
    return f"{fam}-{int(num)}" + (f"({int(enh)})" if enh else "")


def _policy_matrix_rows() -> Iterator[Tuple[str, int, str, List[str]]]:
    for name in sorted(os.listdir(_POLICIES)):
        if not name.endswith(".md"):
            continue
        path = os.path.join(_POLICIES, name)
        in_matrix = False
        for lineno, line in _lines(path):
            if line.startswith("## "):
                in_matrix = line.startswith("## Appendix A")
                continue
            match = _MATRIX_ROW.match(line)
            if in_matrix and match:
                ctrl = _norm_ctrl(*match.groups())
                ccis = [f"CCI-{d}" for d in _CCI.findall(line)]
                yield path, lineno, ctrl, ccis


class TestTemplateCciCitations(unittest.TestCase):
    """CCI citation format, range, and DISA Rev. 5 mapping checks across shipped templates."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.by_ctrl, cls.deprecated = _load_disa_cci_map()

    def test_guard_scans_the_policy_templates(self) -> None:
        """The guard must not pass vacuously because the template tree moved."""
        policies = [p for p in _template_files() if os.path.dirname(p) == _POLICIES]
        self.assertEqual(len(policies), 20)

    def test_no_bare_cci_lists(self) -> None:
        """CCIs are cited as CCI-000001, never as '(CCIs: 000001, ...)'."""
        offenders = [
            _where(path, lineno)
            for path in _template_files()
            for lineno, line in _lines(path)
            if _BARE_FORM.search(line)
        ]
        self.assertEqual(offenders, [], "Bare CCI lists found; use CCI-000001 form:\n" + "\n".join(offenders))

    def test_cci_identifiers_are_six_digits(self) -> None:
        """Every CCI identifier has exactly six digits."""
        offenders = [
            f"{_where(path, lineno)} CCI-{digits}"
            for path in _template_files()
            for lineno, line in _lines(path)
            for digits in _CCI.findall(line)
            if len(digits) != 6
        ]
        self.assertEqual(offenders, [], "Malformed CCI identifiers:\n" + "\n".join(offenders))

    def test_no_cci_above_validated_range(self) -> None:
        """No template cites a CCI above CCI-005169."""
        offenders = [
            f"{_where(path, lineno)} CCI-{digits}"
            for path in _template_files()
            for lineno, line in _lines(path)
            for digits in _CCI.findall(line)
            if int(digits) > _MAX_VALID_CCI
        ]
        self.assertEqual(offenders, [], f"CCIs above CCI-{_MAX_VALID_CCI:06d}:\n" + "\n".join(offenders))

    def test_every_policy_matrix_row_cites_ccis(self) -> None:
        """Each Appendix A row carries one well-formed CCI group."""
        offenders = []
        for name in sorted(os.listdir(_POLICIES)):
            path = os.path.join(_POLICIES, name)
            in_matrix = False
            for lineno, line in _lines(path):
                if line.startswith("## "):
                    in_matrix = line.startswith("## Appendix A")
                    continue
                if in_matrix and _MATRIX_ROW.match(line) and len(_CCI_GROUP.findall(line)) != 1:
                    offenders.append(_where(path, lineno))
        self.assertEqual(offenders, [], "Matrix rows without exactly one CCI group:\n" + "\n".join(offenders))

    def test_no_deprecated_ccis_in_policy_matrices(self) -> None:
        """No Appendix A row cites a deprecated DISA CCI."""
        offenders = [
            f"{_where(path, lineno)} {cci}"
            for path, lineno, _ctrl, ccis in _policy_matrix_rows()
            for cci in ccis
            if cci in self.deprecated
        ]
        self.assertEqual(offenders, [], "Deprecated CCIs cited in policy matrices:\n" + "\n".join(offenders))

    def test_every_cci_maps_to_its_row_control(self) -> None:
        """Every CCI cited in an Appendix A row belongs to that control in DISA Rev. 5."""
        offenders = []
        for path, lineno, ctrl, ccis in _policy_matrix_rows():
            valid_for_ctrl = self.by_ctrl.get(ctrl, set())
            for cci in ccis:
                if cci not in valid_for_ctrl:
                    offenders.append(f"{_where(path, lineno)} {cci} does not map to {ctrl} in DISA Rev. 5")
        self.assertEqual(offenders, [], "Mismatched CCI -> control citations:\n" + "\n".join(offenders))

    def test_rows_cite_every_published_cci_for_their_control(self) -> None:
        """Every Appendix A row cites the complete set of active DISA Rev. 5 CCIs for its control."""
        offenders = []
        for path, lineno, ctrl, ccis in _policy_matrix_rows():
            missing = sorted(self.by_ctrl.get(ctrl, set()) - set(ccis))
            if missing:
                offenders.append(f"{_where(path, lineno)} {ctrl} missing {', '.join(missing)}")
        self.assertEqual(offenders, [], "Rows missing published DISA Rev. 5 CCIs:\n" + "\n".join(offenders))

    def test_cmvp_numbers_allowlisted(self) -> None:
        """Every CMVP certificate number in templates is allowlisted with Active status and metadata."""
        allowlist_path = os.path.join(os.path.dirname(__file__), "fixtures", "cmvp_allowlist.json")
        with open(allowlist_path, encoding="utf-8") as fh:
            allowlist = json.load(fh)["certificates"]

        for cert_id, meta in allowlist.items():
            for required_key in (
                "vendor", "module_name", "standard", "overall_level", "status", "retrieval_date"
            ):
                self.assertTrue(meta.get(required_key), f"Allowlist entry #{cert_id} missing {required_key}")

        cert_re = re.compile(
            r"(?:CMVP[^.\n]{0,40}?#(\d{4})|Cert(?:ificate)?s?\s*#(\d{4})|#(\d{4})\s*(?:BoringCrypto|Cloud\s+HSM|FIPS))",
            re.IGNORECASE,
        )
        hash_cert_re = re.compile(r"#(3101|3622|4407|4735|5104)\b")
        offenders: List[str] = []

        for path in _template_files():
            for lineno, line in _lines(path):
                found = {g for m in cert_re.finditer(line) for g in m.groups() if g}
                found |= set(hash_cert_re.findall(line))
                for num in sorted(found):
                    if num not in allowlist:
                        offenders.append(f"{_where(path, lineno)}: unapproved CMVP #{num}")
                    elif allowlist[num].get("status") != "Active" and "active" in line.lower():
                        offenders.append(f"{_where(path, lineno)}: non-Active CMVP #{num} labelled Active")

        self.assertEqual(offenders, [], "CMVP certificate violations:\n" + "\n".join(offenders))

    def test_no_hsm_140_3_in_templates(self) -> None:
        """No template claims FIPS 140-3 within 60 chars of HSM or Level 3, or attributes KMS to CNSSI 4005."""
        hsm_140_3_re = re.compile(
            r"140-3.{0,60}(?:HSM|Level\s*3)|(?:HSM|Level\s*3).{0,60}140-3",
            re.IGNORECASE,
        )
        offenders: List[str] = []
        for path in _template_files():
            for lineno, line in _lines(path):
                if hsm_140_3_re.search(line):
                    offenders.append(f"{_where(path, lineno)}: 140-3 within 60 chars of HSM/Level 3")
                if "#3101" in line or "#3622" in line:
                    offenders.append(f"{_where(path, lineno)}: forbidden Historical CMVP #3101/#3622")
                if os.path.dirname(path) == _POLICIES and "CNSSI 4005" in line:
                    offenders.append(f"{_where(path, lineno)}: policy misattributes Cloud KMS/HSM to CNSSI 4005")
        self.assertEqual(offenders, [], "HSM FIPS level / CNSSI 4005 violations:\n" + "\n".join(offenders))

    def test_cmvp_function_scope(self) -> None:
        """Each allowlisted CMVP certificate is cited only for its permitted functions."""
        allowlist_path = os.path.join(os.path.dirname(__file__), "fixtures", "cmvp_allowlist.json")
        with open(allowlist_path, encoding="utf-8") as fh:
            allowlist = json.load(fh)["certificates"]

        offenders: List[str] = []
        for path in _template_files():
            for lineno, line in _lines(path):
                for cert_id, meta in allowlist.items():
                    if f"#{cert_id}" not in line:
                        continue
                    for pat in meta.get("prohibited_line_patterns", []):
                        if re.search(pat, line, re.IGNORECASE):
                            offenders.append(
                                f"{_where(path, lineno)}: CMVP #{cert_id} paired with prohibited function pattern {pat!r}"
                            )
        self.assertEqual(offenders, [], "CMVP function-scope violations:\n" + "\n".join(offenders))

    def test_no_withdrawn_controls_asserted(self) -> None:
        """No policy or template asserts withdrawn Rev. 5 controls (such as AT-5 or PL-2(1)) as implemented."""
        withdrawn_re = re.compile(r"\b(?:AT-0?5|PL-0?2\(0?1\))\b")
        offenders: List[str] = []
        for path in _template_files():
            for lineno, line in _lines(path):
                if withdrawn_re.search(line) and "withdrawn" not in line.lower():
                    offenders.append(f"{_where(path, lineno)}: {line.strip()}")
        self.assertEqual(offenders, [], "Withdrawn controls asserted without 'withdrawn' note:\n" + "\n".join(offenders))


if __name__ == "__main__":
    unittest.main()
