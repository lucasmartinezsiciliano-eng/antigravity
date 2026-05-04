from fpdf import FPDF
from fpdf.enums import XPos, YPos

class PDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 11)
        self.set_fill_color(30, 30, 30)
        self.set_text_color(255, 255, 255)
        self.cell(0, 10, "  Big Data - Les 10 V's", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="L", fill=True)
        self.set_text_color(0, 0, 0)
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Pagina {self.page_no()}", align="C")

pdf = PDF()
pdf.set_margins(20, 20, 20)
pdf.add_page()

# TITULO
pdf.set_font("Helvetica", "B", 18)
pdf.set_text_color(20, 20, 20)
pdf.cell(0, 12, "Activitats: Big Data", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
pdf.set_font("Helvetica", "", 10)
pdf.set_text_color(100, 100, 100)
pdf.cell(0, 6, "Informatica - Curs 2025-2026", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
pdf.ln(8)

pdf.set_draw_color(200, 200, 200)
pdf.set_line_width(0.5)
pdf.line(20, pdf.get_y(), 190, pdf.get_y())
pdf.ln(8)

# EXERCICI 5
pdf.set_font("Helvetica", "B", 13)
pdf.set_text_color(255, 255, 255)
pdf.set_fill_color(40, 40, 40)
pdf.cell(0, 9, "  Exercici 5 - Les 10 V's del Big Data", new_x=XPos.LMARGIN, new_y=YPos.NEXT, fill=True)
pdf.ln(4)

pdf.set_font("Helvetica", "", 10)
pdf.set_text_color(60, 60, 60)
pdf.multi_cell(
    0, 6,
    "A continuacio es resumeix el significat de cadascuna de les 10 V's que defineixen el Big Data, "
    "tal com apareixen a la infografia de referencia:",
    new_x=XPos.LMARGIN, new_y=YPos.NEXT
)
pdf.ln(4)

vs = [
    ("1", "Volum",
     "Fa referencia a la gran quantitat de dades que es generen cada segon a escala mundial. "
     "El volum es la caracteristica mes coneguda del Big Data: parlem de terabytes, petabytes o fins i tot "
     "exabytes de dades que cal emmagatzemar i processar."),
    ("2", "Velocitat",
     "Es la rapidesa amb que es generen, transfereixen i han de ser processades les dades. "
     "En molts casos cal analitzar-les en temps real (per exemple, transaccions bancaries o xarxes socials) "
     "per prendre decisions immediates."),
    ("3", "Varietat",
     "Les dades provenen de fonts i formats molt diversos: estructurades (bases de dades), "
     "semiestructurades (XML, JSON) i no estructurades (imatges, videos, correus electronics, audios). "
     "Gestionar aquesta diversitat es un dels grans reptes del Big Data."),
    ("4", "Variabilitat",
     "El significat de les dades pot canviar depenent del context en que s'interpreten. "
     "Un mateix text pot tenir significats molt diferents segons el moment o la situacio, "
     "cosa que dificulta l'analisi automatitzada."),
    ("5", "Veracitat",
     "Es refereix a la fiabilitat i precisio de les dades. No totes les dades disponibles "
     "son exactes o de confianca; per tant, cal aplicar mecanismes de verificacio per assegurar "
     "que la informacio es correcta abans d'usar-la per prendre decisions."),
    ("6", "Valor",
     "El valor es la V mes important: de res serveix tenir moltes dades si no s'obtenen "
     "coneixements utils. El Big Data te valor quan permet prendre millors decisions, "
     "optimitzar processos o descobrir oportunitats de negoci."),
    ("7", "Visualitzacio",
     "La capacitat de representar graficament les dades (grafics, mapes, dashboards) "
     "es clau per facilitar la comprensio humana d'informacio complexa i afavorir "
     "la presa de decisions basada en dades."),
    ("8", "Validacio",
     "Proces de verificacio que les dades compleixen els estandards de qualitat requerits "
     "abans del seu processament. Inclou eliminar duplicats, corregir errors i assegurar "
     "la coherencia de la informacio."),
    ("9", "Volatilitat",
     "Indica durant quant de temps les dades continuen sent rellevants i utils. "
     "Algunes dades perden valor molt rapidament (per exemple, el preu d'una accio), "
     "mentre que d'altres mantenen la seva validesa durant anys."),
    ("10", "Vulnerabilitat",
     "Fa referencia als riscos de seguretat i privacitat associats al tractament de "
     "grans volums de dades. Cal implementar mesures de proteccio robustes per evitar "
     "filtracions, accessos no autoritzats o atacs informatics."),
]

for num, titol, desc in vs:
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(20, 20, 20)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 7, f"  V{num} - {titol}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, fill=True)
    pdf.set_font("Helvetica", "", 9.5)
    pdf.set_text_color(60, 60, 60)
    pdf.set_x(24)
    pdf.multi_cell(166, 5.5, desc, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)

# EXERCICI 6
pdf.ln(4)
pdf.set_font("Helvetica", "B", 13)
pdf.set_text_color(255, 255, 255)
pdf.set_fill_color(40, 40, 40)
pdf.cell(0, 9, "  Exercici 6 - Nike Wearables: dades addicionals", new_x=XPos.LMARGIN, new_y=YPos.NEXT, fill=True)
pdf.ln(4)

pdf.set_font("Helvetica", "", 10)
pdf.set_text_color(60, 60, 60)
pdf.multi_cell(
    0, 6,
    "Nike ofereix dispositius wearables que ja registren dades com la frequencia cardiaca i la distancia "
    "recorreguda. A continuacio es proposen cinc dades addicionals que podrien ser d'interes per als seus clients:",
    new_x=XPos.LMARGIN, new_y=YPos.NEXT
)
pdf.ln(5)

dades = [
    ("1", "Nivell d'oxigen en sang (SpO2)",
     "Mesura la saturacio d'oxigen a la sang durant l'exercici. Especialment rellevant "
     "per a atletes d'alta muntanya o de resistencia, ja que indica si el cos rep l'oxigen "
     "suficient i alerta sobre possibles riscos de sobreesforc."),
    ("2", "Variabilitat de la frequencia cardiaca (HRV)",
     "L'HRV es un indicador precis del nivell de recuperacio i de l'estres del sistema "
     "nerviós autònom. Permet als esportistes saber si estan preparats per entrenar "
     "intensament o si necessiten descansar per evitar lesions."),
    ("3", "Temperatura corporal",
     "Monitorar la temperatura durant l'exercici ajuda a detectar situacions de "
     "sobreescalfament (cop de calor) o hipotermia en condicions de fred extrem. "
     "Proporciona informacio sobre com s'adapta el cos a l'entorn."),
    ("4", "Qualitat del son",
     "L'analisi de les fases del son (REM, son profund, son lleuger) permet entendre "
     "com es recupera l'esportista. Una bona recuperacio nocturna es clau per millorar "
     "el rendiment esportiu i prevenir el sobreentrenament."),
    ("5", "Nivell d'hidratacio",
     "Detectar el nivell d'hidratacio de l'esportista en temps real permet prevenir "
     "la deshidratacio, que redueix el rendiment i pot ser perillosa. Alguns sensors "
     "avancats ja poden estimar-la a traves de la suor o la impedancia de la pell."),
]

for num, titol, desc in dades:
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(20, 20, 20)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 7, f"  {num}. {titol}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, fill=True)
    pdf.set_font("Helvetica", "", 9.5)
    pdf.set_text_color(60, 60, 60)
    pdf.set_x(24)
    pdf.multi_cell(166, 5.5, desc, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)

# PIE
pdf.ln(6)
pdf.set_draw_color(200, 200, 200)
pdf.line(20, pdf.get_y(), 190, pdf.get_y())
pdf.ln(4)
pdf.set_font("Helvetica", "I", 8.5)
pdf.set_text_color(130, 130, 130)
pdf.cell(0, 5, "Fonts: Infografia 'Les 10 V del Big Data' (bit.ly/10_bigdata) - Elaboracio propia",
         new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")

out = r"C:\Users\Pc2025\Desktop\Activitats_BigData_10V.pdf"
pdf.output(out)
print(f"PDF generat: {out}")
