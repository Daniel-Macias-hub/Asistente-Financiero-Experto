from conocimiento.database import get_connection
import sqlite3

def pre_cargar_conocimiento():
    """Inyecta datos iniciales a la base de conocimientos para demostración."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Limpiar datos anteriores para asegurar carga limpia de nuevos conceptos
    cursor.execute("DELETE FROM relaciones")
    cursor.execute("DELETE FROM sinonimos")
    cursor.execute("DELETE FROM reglas")
    cursor.execute("DELETE FROM conceptos")
    cursor.execute("DELETE FROM preguntas_frecuentes")
    
    conceptos = [
        # Conceptos originales
        ("accion", "Parte alícuota del capital social de una sociedad anónima."),
        ("etf", "Exchange Traded Fund. Fondo de inversión que cotiza en bolsa como si fuera una acción."),
        ("riesgo", "Probabilidad de que una inversión produzca un retorno menor al esperado o pierda valor."),
        ("diversificacion", "Estrategia de inversión que consiste en distribuir el capital en distintos activos para reducir el riesgo global."),
        ("s&p 500", "Índice bursátil que representa a las 500 empresas más grandes de Estados Unidos."),
        ("nasdaq", "Índice bursátil que agrupa a las principales empresas tecnológicas."),
        ("renta fija", "Inversiones donde se conoce de antemano el interés a recibir, como los bonos."),
        ("renta variable", "Inversiones donde no se conoce la rentabilidad futura, como las acciones."),
        ("inflacion", "Aumento generalizado y sostenido de los precios de bienes y servicios en un país durante un periodo de tiempo, lo que reduce el poder adquisitivo."),
        
        # Nuevos conceptos
        ("bono", "Instrumento de renta fija que representa un préstamo hecho por un inversor a un emisor (generalmente gubernamental o corporativo)."),
        ("dividendo", "Proporción de ganancias de una empresa distribuida periódicamente a sus accionistas."),
        ("portafolio", "Cartera o colección de activos financieros en propiedad de un individuo o institución."),
        ("liquidez", "Facilidad y rapidez con la que un activo financiero puede ser comprado o vendido sin alterar significativamente su precio."),
        ("volatilidad", "Medida de la frecuencia e intensidad de las variaciones del precio de un activo."),
        ("mercado de valores", "Espacio físico o virtual donde los agentes compran y venden acciones, bonos y otros valores financieros."),
        ("bull market", "Mercado alcista, caracterizado por una tendencia sostenida al alza de los precios de las acciones o activos."),
        ("bear market", "Mercado bajista, caracterizado por una tendencia prolongada a la baja y caídas de precios."),
        ("broker", "Intermediario financiero autorizado para realizar operaciones de compra y venta de valores por cuenta de sus clientes."),
        ("rendimiento", "Ganancia o retorno financiero obtenido de una inversión, generalmente expresado en porcentaje anual."),
        ("interes compuesto", "Efecto financiero donde los intereses generados se suman al capital inicial para producir nuevos intereses en periodos sucesivos."),
        ("tasa de interes", "Precio cobrado por el uso del dinero ajeno, expresado habitualmente como porcentaje anual de un crédito o ahorro."),
        ("banco central", "Entidad pública responsable de gestionar la moneda y la política monetaria de una nación."),
        ("tipo de cambio", "Relación de valor o precio entre dos monedas o divisas de diferentes países."),
        ("criptomoneda", "Moneda digital basada en tecnología de criptografía y cadenas de bloques, descentralizada y sin intermediarios tradicionales."),
        ("bitcoin", "La primera y más grande criptomoneda descentralizada basada en la tecnología blockchain."),
        ("fondos de inversion", "Mecanismos de inversión colectiva que reúnen fondos de múltiples inversionistas para invertirlos en diversos instrumentos financieros."),
        ("deuda", "Obligación financiera contraída por un individuo, empresa o gobierno de devolver una cantidad de dinero prestada más intereses."),
        ("capital", "Recursos financieros o activos que se poseen e invierten para generar riqueza o iniciar un negocio."),
        ("activo", "Recurso económico que posee una entidad o persona natural del cual se esperan obtener beneficios o rendimientos futuros."),
        ("pasivo", "Conjunto de deudas y obligaciones financieras que posee una persona o empresa."),
        ("patrimonio", "Diferencia aritmética entre la suma de todos los activos y la suma de todos los pasivos de una entidad."),
        ("utilidad", "Ganancia o beneficio neto obtenido tras restar todos los gastos y costos de los ingresos totales."),
        ("perdida", "Disminución neta del valor financiero o resultado negativo en una operación o ejercicio contable."),
        ("precio", "Valor monetario que se asigna a un bien, servicio o activo financiero en el mercado."),
        ("oferta", "Cantidad total de un bien o servicio que los vendedores están dispuestos a vender a un precio determinado."),
        ("demanda", "Cantidad de bienes o servicios que los compradores desean y tienen la capacidad de adquirir a diferentes niveles de precios."),
        ("presupuesto", "Planificación y estimación formal de los ingresos y gastos financieros en un periodo específico."),
        ("ahorro", "Parte de los ingresos que no se destina al gasto de consumo inmediato y se reserva para contingencias o inversiones futuras."),
        ("inversion", "Uso de recursos financieros o capital con el fin de adquirir activos que generen valor, renta o dividendos en el futuro."),
        ("pension", "Prestación económica de carácter periódico y vitalicio concedida a un trabajador tras su jubilación o incapacidad."),
        ("seguro", "Contrato financiero por el cual una entidad aseguradora cubre un riesgo o siniestro a cambio del pago de una prima regular."),
        ("tasa de desempleo", "Proporción de la población activa que busca trabajo de forma activa pero no lo encuentra."),
        ("pib", "Producto Interno Burto (PIB). Medida del valor de mercado de todos los bienes y servicios finales producidos en un país durante un año."),
        ("recesion", "Periodo de declive económico generalizado caracterizado por la disminución del PIB durante al menos dos trimestres consecutivos."),
        ("deflacion", "Caída generalizada y prolongada del nivel de precios de los bienes y servicios, contraria a la inflación."),
        ("rentabilidad", "Capacidad de una inversión o actividad económica de generar utilidades o rendimientos superiores al capital invertido."),
        ("apalancamiento", "Uso de endeudamiento o dinero prestado para financiar una inversión con el fin de incrementar su rentabilidad potencial."),
        ("arbitraje", "Estrategia financiera de comprar y vender simultáneamente un mismo activo en diferentes mercados para aprovechar discrepancias de precio."),
        ("comision", "Porcentaje o tarifa fija cobrada por un broker o intermediario financiero por realizar una transacción bursátil.")
    ]
    
    relaciones = [
        ("etf", "diversificacion", "permite"),
        ("diversificacion", "riesgo", "reduce"),
        ("s&p 500", "renta variable", "es un tipo de"),
        ("accion", "renta variable", "es un tipo de"),
        
        # Nuevas relaciones
        ("bono", "renta fija", "es un tipo de"),
        ("inflacion", "liquidez", "afecta negativamente"),
        ("interes compuesto", "ahorro", "potencia"),
        ("bitcoin", "criptomoneda", "es el principal exponente de"),
        ("criptomoneda", "riesgo", "posee alto"),
        ("broker", "accion", "permite comprar"),
        ("broker", "etf", "permite comprar"),
        ("dividendo", "accion", "es pagado por"),
        ("portafolio", "diversificacion", "se beneficia de"),
        ("recesion", "pib", "se caracteriza por la caida del"),
        ("deflacion", "inflacion", "es el fenomeno opuesto a la"),
        ("apalancamiento", "riesgo", "incrementa el")
    ]
    
    reglas = [
        ("reducir riesgo", "Se recomienda emplear la diversificación de activos"),
        ("que es etf", "Un ETF es una excelente forma de diversificar"),
        ("invertir tecnologia", "El índice NASDAQ agrupa a las principales empresas tecnológicas"),
        
        # Nuevas reglas
        ("que es inflacion", "La inflacion reduce el valor de tu dinero a lo largo del tiempo, por lo que es aconsejable invertir para proteger tu poder adquisitivo."),
        ("que es accion", "Las acciones representan propiedad en una empresa y forman parte de la renta variable."),
        ("que es bono", "Los bonos son instrumentos de renta fija que ofrecen menor riesgo comparado con las acciones."),
        ("que es interes compuesto", "El interes compuesto multiplica tu capital exponencialmente porque los intereses ganados vuelven a generar nuevos intereses."),
        ("como ahorrar", "Para ahorrar dinero es recomendable elaborar un presupuesto mensual y destinar un porcentaje fijo a una cuenta de ahorro o inversion."),
        ("que es criptomoneda", "Las criptomonedas como bitcoin son activos digitales altamente volatiles y con un riesgo elevado."),
        ("que es diversificacion", "Diversificar disminuye el riesgo al distribuir tu dinero entre diferentes instrumentos como acciones, bonos y ETFs."),
        ("mercado alcista", "En un bull market o mercado alcista, el optimismo predomina y los precios tienden a subir de forma sostenida."),
        ("mercado bajista", "En un bear market o mercado bajista, el pesimismo predomina y los precios sufren caidas prolongadas."),
        ("que es recesion", "Una recesion es cuando la economia de un pais decrece durante al menos dos trimestres, afectando empleos e inversiones."),
        ("que es pib", "El Producto Interno Bruto o PIB mide el tamaño y la salud de la economia de un pais.")
    ]
    
    sinonimos = [
        # Originales
        ("accion", "acciones"),
        ("etf", "etfs"),
        ("etf", "e te efe"),
        ("etf", "eiti efe"),
        ("etf", "fondo indexado"),
        ("etf", "fondo cotizado"),
        ("s&p 500", "ese y pe quinientos"),
        ("nasdaq", "nas dac"),
        ("riesgo", "riesgos"),
        ("diversificacion", "diversificar"),
        ("inflacion", "alza de precios"),
        ("inflacion", "inflaciones"),
        
        # Nuevos sinónimos (sin acentos, en minúsculas)
        ("bono", "bonos"),
        ("bono", "bono del tesoro"),
        ("bono", "bono corporativo"),
        ("bono", "titulos de deuda"),
        ("dividendo", "dividendos"),
        ("dividendo", "pago de dividendos"),
        ("dividendo", "reparto de dividendos"),
        ("portafolio", "portafolios"),
        ("portafolio", "cartera de inversion"),
        ("portafolio", "cartera de inversiones"),
        ("liquidez", "liquido"),
        ("liquidez", "dinero disponible"),
        ("liquidez", "facilidad de pago"),
        ("volatilidad", "volatil"),
        ("volatilidad", "variacion de precio"),
        ("volatilidad", "fluctuacion"),
        ("mercado de valores", "bolsa de valores"),
        ("mercado de valores", "la bolsa"),
        ("mercado de valores", "mercado bursatil"),
        ("bull market", "mercado alcista"),
        ("bull market", "tendencia alcista"),
        ("bull market", "mercado en alza"),
        ("bear market", "mercado bajista"),
        ("bear market", "tendencia bajista"),
        ("bear market", "mercado en baja"),
        ("broker", "brokers"),
        ("broker", "corredor de bolsa"),
        ("broker", "plataforma de inversion"),
        ("rendimiento", "rendimientos"),
        ("rendimiento", "retorno de inversion"),
        ("rendimiento", "retorno"),
        ("rendimiento", "ganancia"),
        ("interes compuesto", "intereses compuestos"),
        ("interes compuesto", "efecto bola de nieve"),
        ("tasa de interes", "tasas de interes"),
        ("tasa de interes", "tasa de interes"),
        ("tasa de interes", "costo del dinero"),
        ("banco central", "bancos centrales"),
        ("banco central", "reserva federal"),
        ("banco central", "fed"),
        ("banco central", "banxico"),
        ("tipo de cambio", "tasa de cambio"),
        ("tipo de cambio", "paridad cambiaria"),
        ("tipo de cambio", "valor del dolar"),
        ("criptomoneda", "criptomonedas"),
        ("criptomoneda", "monedas virtuales"),
        ("criptomoneda", "cripto"),
        ("criptomoneda", "criptos"),
        ("criptomoneda", "crypto"),
        ("bitcoin", "btc"),
        ("bitcoin", "bitcoins"),
        ("fondos de inversion", "fondo de inversion"),
        ("fondos de inversion", "fondos mutuos"),
        ("fondos de inversion", "fondo mutuo"),
        ("deuda", "deudas"),
        ("deuda", "prestamo"),
        ("deuda", "prestamos"),
        ("deuda", "credito"),
        ("deuda", "creditos"),
        ("capital", "capitales"),
        ("capital", "patrimonio inicial"),
        ("capital", "recursos propios"),
        ("activo", "activos"),
        ("activo", "bienes"),
        ("pasivo", "pasivos"),
        ("pasivo", "obligaciones"),
        ("patrimonio", "patrimonio neto"),
        ("patrimonio", "capital contable"),
        ("utilidad", "utilidades"),
        ("utilidad", "beneficio"),
        ("utilidad", "beneficio neto"),
        ("utilidad", "ganancia neta"),
        ("perdida", "perdidas"),
        ("perdida", "deficit"),
        ("perdida", "resultado negativo"),
        ("precio", "precios"),
        ("precio", "costo"),
        ("precio", "valor"),
        ("oferta", "ofertas"),
        ("oferta", "disponibilidad"),
        ("demanda", "demandas"),
        ("demanda", "peticion"),
        ("demanda", "compras"),
        ("presupuesto", "presupuestos"),
        ("presupuesto", "plan financiero"),
        ("ahorro", "ahorros"),
        ("ahorro", "guardar dinero"),
        ("ahorro", "dinero guardado"),
        ("inversion", "inversiones"),
        ("inversion", "invertir"),
        ("inversion", "colocar capital"),
        ("pension", "pensiones"),
        ("pension", "jubilacion"),
        ("pension", "retiro"),
        ("seguro", "seguros"),
        ("seguro", "poliza"),
        ("seguro", "polizas"),
        ("tasa de desempleo", "desempleo"),
        ("tasa de desempleo", "paro"),
        ("tasa de desempleo", "tasa de paro"),
        ("pib", "producto interno bruto"),
        ("pib", "pib nacional"),
        ("pib", "crecimiento economico"),
        ("recesion", "recesiones"),
        ("recesion", "crisis economica"),
        ("recesion", "caida economica"),
        ("deflacion", "deflaciones"),
        ("deflacion", "caida de precios"),
        ("rentabilidad", "rentable"),
        ("rentabilidad", "margen de ganancia"),
        ("apalancamiento", "apalancarse"),
        ("apalancamiento", "deuda para invertir"),
        ("arbitraje", "compraventa simultanea"),
        ("comision", "comisiones"),
        ("comision", "costo de operacion")
    ]
    
    preguntas_frecuentes = [
        ("quien eres", "Soy un asistente experto en educación financiera diseñado sin IA comercial, operando 100% offline."),
        ("como funcionas", "Funciono a través de un motor de inferencia basado en reglas y una base de conocimientos local en SQLite.")
    ]
    
    for c in conceptos:
        try: cursor.execute("INSERT INTO conceptos (nombre, definicion) VALUES (?, ?)", c)
        except sqlite3.IntegrityError: pass
        
    for r in relaciones:
        try: cursor.execute("INSERT INTO relaciones (origen, destino, tipo_relacion) VALUES (?, ?, ?)", r)
        except sqlite3.IntegrityError: pass
        
    for reg in reglas:
        try: cursor.execute("INSERT INTO reglas (condicion, conclusion) VALUES (?, ?)", reg)
        except sqlite3.IntegrityError: pass
        
    for s in sinonimos:
        try: cursor.execute("INSERT INTO sinonimos (termino, sinonimo) VALUES (?, ?)", s)
        except sqlite3.IntegrityError: pass
        
    for p in preguntas_frecuentes:
        try: cursor.execute("INSERT INTO preguntas_frecuentes (pregunta, respuesta) VALUES (?, ?)", p)
        except sqlite3.IntegrityError: pass
        
    conn.commit()
    conn.close()
    print("Conocimiento inicial pre-cargado exitosamente.")

if __name__ == "__main__":
    from conocimiento.database import inicializar_db
    inicializar_db()
    pre_cargar_conocimiento()
