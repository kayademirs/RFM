###############################################################
# 1. İş Problemi (Business Problem)
###############################################################

# Bir e-ticaret şirketi müşterilerini segmentlere ayırıp bu segmentlere göre
# pazarlama stratejileri belirlemek istiyor.

# Veri Seti Hikayesi
# https://archive.ics.uci.edu/ml/datasets/Online+Retail+II

# Online Retail II isimli veri seti İngiltere merkezli online bir satış mağazasının
# 01/12/2009 - 09/12/2011 tarihleri arasındaki satışlarını içeriyor.


# Değişkenler

# InvoiceNo: Fatura numarası. Her işleme yani faturaya ait eşsiz numara. C ile başlıyorsa iptal edilen işlem.
# StockCode: Ürün kodu. Her bir ürün için eşsiz numara.
# Description: Ürün ismi
# Quantity: Ürün adedi. Faturalardaki ürünlerden kaçar tane satıldığını ifade etmektedir.
# InvoiceDate: Fatura tarihi ve zamanı.
# UnitPrice: Ürün fiyatı (Sterlin cinsinden)
# CustomerID: Eşsiz müşteri numarası
# Country: Ülke ismi. Müşterinin yaşadığı ülke.


import datetime as dt
import pandas as pd
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 500)
pd.set_option('display.float_format', lambda x: '%.4f' % x)


###################################
# Custom function


def segment_describe(rfm, segments):
    for segment in segments:
        print("************* " + segment + " *************")
        print(rfm[rfm["segment"] == segment].describe().T)


##################################
# Görev 1 | Veriyi Anlama ve Hazırlama

# SORU 1: Online Retail II excelindeki 2010-2011 verisini okuyunuz.
# Oluşturduğunuz dataframe’in kopyasını oluşturunuz.
# 2010-2011 yılı içerisindeki veriler


df_ = pd.read_excel("datasets/online_retail_II.xlsx", sheet_name="Year 2010-2011")
df = df_.copy()
df.head()

# SORU 2: Veri setinin betimsel istatistiklerini inceleyiniz.
df.describe().T

# SORU 3: Veri setinde eksik gözlem var mı? Varsa hangi değişkende kaç tane eksik gözlem vardır?
df.isnull().any()
df.isnull().sum()

# SORU 4: Eksik gözlemleri veri setinden çıkartınız. Çıkarma işleminde ‘inplace=True’ parametresini kullanınız.
df.dropna(inplace=True)

# SORU 5: Eşsiz ürün sayısı kaçtır?
df['StockCode'].nunique()

# SORU 6: Hangi üründen kaçar tane vardır?
df['StockCode'].value_counts()

# SORU 7: En çok sipariş edilen 5 ürünü çoktan aza doğru sıralayınız.
df.groupby(["StockCode", "Description"]).agg({"Quantity": "sum"}).sort_values(by="Quantity", ascending=False).head(10)

####################################
today_date = dt.datetime(2011, 12, 11)
df['TotalPrice'] = df['Quantity'] * df['Price']
ndf = df.groupby(['Customer ID']).agg({'InvoiceDate': lambda date: (today_date - date.max()).days,
                                       'Invoice': lambda num: num.nunique(),
                                       'TotalPrice': lambda price: price.sum()})

ndf.columns = ['recency', 'frequency', "monetary"]
ndf = ndf[(ndf['monetary'] > 0)]
ndf.head()

####################################
# SORU 8: Faturalardaki ‘C’ iptal edilen işlemleri göstermektedir. İptal edilen işlemleri veri setinden çıkartınız.
# df.groupby(["StockCode", "Description"]).agg({"Quantity": "sum"}).sort_values(by="Quantity", ascending=False).head(10)
df = df[~df["Invoice"].str.contains("C", na=False)]
df.head()
# SORU 9: Fatura başına elde edilen toplam kazancı ifade eden ‘TotalPrice’ adında bir değişken oluşturunuz.
df['TotalPrice'] = df['Quantity'] * df['Price']

##################################
# Görev 2 | RFM metriklerinin hesaplanması

rfm = df.groupby('Customer ID').agg({'InvoiceDate': lambda date: (today_date - date.max()).days,
                                     'Invoice': lambda num: num.nunique(),
                                     "TotalPrice": lambda price: price.sum()})
rfm.columns = ['recency', 'frequency', "monetary"]
rfm = rfm[(rfm['monetary'] > 0)]
rfm.head()
##################################
# Görev 3 | RFM skorlarının oluşturulması ve tek bir değişkene çevrilmesi

def rfm_score(rfm):
    rfm["recency_score"] = pd.qcut(rfm['recency'], 5, labels=[5, 4, 3, 2, 1])
    rfm["frequency_score"] = pd.qcut(rfm['frequency'].rank(method="first"), 5, labels=[1, 2, 3, 4, 5])
    rfm["monetary_score"] = pd.qcut(rfm['monetary'], 5, labels=[1, 2, 3, 4, 5])

    rfm["RFM_SCORE"] = (rfm['recency_score'].astype(str) +
                        rfm['frequency_score'].astype(str))

    return rfm

ndf = rfm_score(ndf)
rfm = rfm_score(rfm)
##################################
# Görev 4 | RFM skorlarının segment olarak tanımlanması

def segmentaion(rfm):
    seg_map = {
        r'[1-2][1-2]': 'hibernating',
        r'[1-2][3-4]': 'at_Risk',
        r'[1-2]5': 'cant_loose',
        r'3[1-2]': 'about_to_sleep',
        r'33': 'need_attention',
        r'[3-4][4-5]': 'loyal_customers',
        r'41': 'promising',
        r'51': 'new_customers',
        r'[4-5][2-3]': 'potential_loyalists',
        r'5[4-5]': 'champions'
    }

    rfm['segment'] = rfm['RFM_SCORE'].replace(seg_map, regex=True)
    return rfm


rfm = segmentaion(rfm)
ndf = segmentaion(ndf)

##################################
# Görev 5 | Aksiyon zamanı!
# Önemli bulduğunuz 3 segmenti seçiniz. Bu üç segmenti;

rfm.groupby("segment").agg({'segment': 'count',
                            'recency': ['mean', 'median', 'min', 'max'],
                            'frequency': ['mean', 'median', 'min', 'max'],
                            'monetary': ['mean', 'median', 'min', 'max']}).\
    sort_values(by=('segment', 'count'), ascending=False, axis=0)

ndf.groupby("segment").agg({'segment': 'count',
                            'recency': ['mean', 'median', 'min', 'max'],
                            'frequency': ['mean', 'median', 'min', 'max'],
                            'monetary': ['mean', 'median', 'min', 'max']}).\
    sort_values(by=('segment', 'count'), ascending=False, axis=0)


segment_describe(rfm, ['hibernating', 'potential_loyalists'])
segment_describe(ndf, ['hibernating', 'potential_loyalists'])

# En fazla müşteri 1071 değeri ile hibernating segmentinde bulunmaktadır.
# recency ve frequency değerlerine baktığımızda daha önce sık sık alışveriş
# yapan müşterileri kaybetmek üzere olduğumuz görülmektedir.
# Monetary değeri göz önünde bulundurulursa bu grup daha detaylı bir şekilde incelenmelidir
# Monetary değerinin standart sapmasının çok yüksek olduğu gözlemlenmedir. Segmentin tamamına odaklanmak yerine
# eşik değeri belirlenip (örneğin manetary değeri %75 çeyreklik değerinin üzerinde olması)
# bu eşik değerinin üzerinde kalan kişilere özel teklif verilmesi
# iş yükü ve veririmlik açısından daha karlı bir yöntem olabilir

# potential_loyalists segmenti önemli bir segment bu segmentin bir kısmını loyal customers
# bir kısmını ise champions segmentine yükseltebiliriz frequency değeri ortalama olan bu segmenti
# promosyon ve kampanyalar ile daha çok alışveriş yapmaya teşvik edebiliriz.
# bu segmentte bulunun kişilerin alışveriş alışkanlıkları incelenerek
# alışkanlıklara göre bir sınıflandırmaya gidilip özelleştirilmiş teklifler sunulabilir.

# new customer segmenti
# yeni müşteri kampanyaları düzenlenebilir
# örneğin ilk 3 alışverişinizde kargo bedava veya belli bir indirim yüzdesi verilebilir


# "Loyal Customers" sınıfına ait customer ID'leri seçerek excel çıktısını alınız.

rfm[rfm["segment"] == "loyal_customers"]
new_df = pd.DataFrame()
new_df["new_customer_id"] = rfm[rfm["segment"] == "loyal_customers"].index
new_df.head()

new_df.to_csv("loyal_customers.csv")  # df'i kaydet


