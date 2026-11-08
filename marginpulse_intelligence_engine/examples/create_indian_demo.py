"""Synthetic FMCG distributor (fictional) for an Indian client demo. INR, GST-style columns, Tally/Busy-style headers."""
import numpy as np, pandas as pd
from datetime import date, timedelta
rng=np.random.default_rng(2026)
START,END=date(2025,11,1),date(2026,10,31)
prods=[ # code,name,category,uom,hsn,gst,cost,price,supplier,reorder
("P001","Basmati Rice 5kg","Staples","Bag","1006",5,365,455,"S01",60),("P002","Toor Dal 1kg","Staples","Pack","0713",5,128,158,"S01",120),
("P003","Sunflower Oil 1L","Staples","Pouch","1512",5,118,142,"S02",200),("P004","Atta 10kg","Staples","Bag","1101",5,372,436,"S01",80),
("P005","Sugar 1kg","Staples","Pack","1701",5,41,49,"S01",300),("P006","Tea 500g","Beverages","Pack","0902",5,218,272,"S03",90),
("P007","Instant Coffee 100g","Beverages","Jar","2101",18,198,255,"S03",70),("P008","Fruit Juice 1L","Beverages","Pack","2009",12,66,88,"S04",150),
("P009","Biscuits Family Pack","Snacks","Pack","1905",18,24,31,"S05",400),("P010","Namkeen 400g","Snacks","Pack","2106",12,70,92,"S05",200),
("P011","Instant Noodles 5pk","Snacks","Pack","1902",12,58,74,"S05",250),("P012","Detergent Powder 2kg","Home Care","Pack","3402",18,176,226,"S06",100),
("P013","Dishwash Liquid 750ml","Home Care","Bottle","3402",18,92,121,"S06",120),("P014","Floor Cleaner 1L","Home Care","Bottle","3402",18,88,118,"S06",100),
("P015","Soap 4pk","Personal Care","Pack","3401",18,112,148,"S07",180),("P016","Shampoo 340ml","Personal Care","Bottle","3305",18,158,212,"S07",110),
("P017","Toothpaste 200g","Personal Care","Tube","3306",18,74,98,"S07",200),("P018","Ghee 1L","Dairy","Jar","0405",12,532,640,"S08",60),
("P019","Paneer 200g","Dairy","Pack","0406",5,68,86,"S08",90),("P020","Butter 500g","Dairy","Pack","0405",12,246,298,"S08",70)]
P=pd.DataFrame(prods,columns=["ItemCode","ItemName","ItemGroup","Unit","HSN","GSTRate","Cost","Price","SupplierCode","MinStock"])
sup=[("S01","Fictional Agro Traders Pvt Ltd","Maharashtra",30),("S02","Fictional Edible Oils LLP","Gujarat",21),("S03","Fictional Tea & Coffee Co","Assam",30),("S04","Fictional Beverages Pvt Ltd","Karnataka",15),
("S05","Fictional Foods Ltd","Maharashtra",30),("S06","Fictional Home Products Pvt Ltd","Gujarat",45),("S07","Fictional Personal Care Ltd","Maharashtra",30),("S08","Fictional Dairy Cooperative","Maharashtra",7)]
S=pd.DataFrame(sup,columns=["SupplierCode","SupplierName","State","CreditDays"])
segs=["Kirana","Supermarket","Wholesaler","HoReCa"]; states=["Maharashtra"]*22+["Gujarat"]*4+["Karnataka"]*4
cust=[]
for i in range(1,31):
    seg=segs[i%4]; terms={"Kirana":15,"Supermarket":45,"Wholesaler":30,"HoReCa":30}[seg]
    cust.append((f"C{i:03d}",f"Fictional {seg} Customer {i:02d}",seg,states[i-1],terms,int(rng.choice([50000,100000,250000,500000]))))
C=pd.DataFrame(cust,columns=["CustomerCode","CustomerName","Segment","State","CreditDays","CreditLimit"])
slow=set(["C007","C019"]); bad={"C023"}
months=pd.period_range("2025-11","2026-10",freq="M")
season={1:1.0,2:1.0,3:.98,4:1.02,5:1.04,6:1.06,7:1.08,8:1.05,9:1.12,10:1.18,11:1.25,12:1.0}
# demand growth ~1%/mo with festive uplift (Oct-Nov); Oct-26 deliberately softer for one segment
rows=[];inv=0
for m in months:
    d0=m.start_time.date(); nd=m.days_in_month
    ninv=int(rng.integers(95,115)*season[m.month]*(1+0.012*list(months).index(m)))
    for _ in range(ninv):
        inv+=1; dt=d0+timedelta(days=int(rng.integers(0,nd))); c=C.sample(1,random_state=int(rng.integers(1e9))).iloc[0]
        for ln,(_,p) in enumerate(P.sample(int(rng.integers(2,6)),random_state=int(rng.integers(1e9))).iterrows(),1):
            q=int(max(2,rng.normal({"Kirana":14,"Supermarket":60,"Wholesaler":90,"HoReCa":30}[c.Segment],6)*season[m.month]*(0.6 if p.ItemGroup=="Dairy" else 1)))
            price=round(p.Price*(1+rng.normal(0,.012)),2); cost=round(p.Cost*(1+0.006*list(months).index(m)/11*(1.0 if p.ItemCode!="P003" else 8)),2)  # P003 oil: real cost creep
            disc=round(price*q*{"Kirana":.01,"Supermarket":.04,"Wholesaler":.03,"HoReCa":.02}[c.Segment],2)
            taxable=round(price*q-disc,2); cogs=round(cost*q,2); gst=round(taxable*p.GSTRate/100,2)
            rows.append([f"INV/{m.year%100}-{(m.year+1)%100 if m.month>3 else m.year%100:02d}/{inv:05d}".replace("INV/25-26","INV/2526").replace("INV/26-27","INV/2627"),ln,dt,c.CustomerCode,p.ItemCode,p.ItemGroup,q,price,disc,taxable,p.GSTRate,gst,cost,cogs,round(taxable-cogs,2),c.State,f"SP{int(rng.integers(1,6)):02d}","INR"])
Sa=pd.DataFrame(rows,columns=["VoucherNo","LineNo","VoucherDate","PartyCode","ItemCode","ItemGroup","Qty","Rate","DiscountAmt","TaxableValue","GSTRate","GSTAmount","UnitCost","CostOfSales","GrossProfit","PlaceOfSupply","Salesperson","Currency"])
# stock simulation + purchases
Sa["m"]=pd.to_datetime(Sa.VoucherDate).dt.to_period("M"); dem=Sa.groupby(["ItemCode","m"]).Qty.sum().unstack(fill_value=0)
pur=[];mov=[];po=0;stock={}
for _,p in P.iterrows():
    stock[p.ItemCode]=int(dem.loc[p.ItemCode,months[0]]*1.4); mov.append([date(2025,11,1),"Opening",f"OB-{p.ItemCode}",p.ItemCode,stock[p.ItemCode],p.Cost])
purchase_cost=lambda p,mi: round(p.Cost*(1+0.006*mi/11*(1.0 if p.ItemCode!="P003" else 8))*(1.0 if not(p.ItemCode=="P003" and mi==11) else 1.0),2)
for mi,m in enumerate(months):
    for _,p in P.iterrows():
        need=int(dem.loc[p.ItemCode,m]); nxt=int(dem.loc[p.ItemCode,months[mi+1]]) if mi<11 else need
        tgt=int(nxt*1.15+p.MinStock*0.2) if p.ItemCode not in("P009","P018") else int(nxt*0.95)  # P009/P018 run lean -> near/below reorder at cut-off
        buy=max(0,tgt-(stock[p.ItemCode]-need)) if True else 0
        # receive early in month BEFORE sales so stock never negative
        stock[p.ItemCode]+=buy
        if buy>0:
            po+=1; dt=m.start_time.date()+timedelta(days=int(rng.integers(0,3))); cst=purchase_cost(p,mi)
            pur.append([f"PO/{po:04d}",1,dt,p.SupplierCode,p.ItemCode,p.ItemGroup,buy,cst,round(buy*cst,2),"INR"]); mov.append([dt,"Purchase",f"PO/{po:04d}",p.ItemCode,buy,cst])
        stock[p.ItemCode]-=need
for _,r in Sa.iterrows(): mov.append([r.VoucherDate,"Sale",r.VoucherNo,r.ItemCode,-int(r.Qty),r.UnitCost])
Pu=pd.DataFrame(pur,columns=["PurchaseNo","LineNo","PurchaseDate","SupplierCode","ItemCode","ItemGroup","Qty","Rate","LineAmount","Currency"])
Mv=pd.DataFrame(mov,columns=["MovementDate","MovementType","ReferenceNo","ItemCode","QtyChange","Rate"]).sort_values(["MovementDate","MovementType"]).reset_index(drop=True)
# small genuine stock adjustments (breakage/shrinkage)
adj=[]
for code in ["P008","P013","P017","P005"]:
    adj.append([date(2026,9,30),"Adjustment",f"ADJ-{code}",code,-int(rng.integers(3,12)),float(P.set_index('ItemCode').Cost[code])])
Mv=pd.concat([Mv,pd.DataFrame(adj,columns=Mv.columns)]).sort_values(["MovementDate","MovementType"]).reset_index(drop=True)
cl=Mv.groupby("ItemCode").QtyChange.sum()
last=Sa.groupby("ItemCode").VoucherDate.max()
Inv=pd.DataFrame({"ItemCode":P.ItemCode,"ItemName":P.ItemName,"ItemGroup":P.ItemGroup,
 "OpeningQty":[Mv[(Mv.ItemCode==c)&(Mv.MovementType=="Opening")].QtyChange.sum() for c in P.ItemCode],
 "InwardQty":[Mv[(Mv.ItemCode==c)&(Mv.MovementType=="Purchase")].QtyChange.sum() for c in P.ItemCode],
 "OutwardQty":[-Mv[(Mv.ItemCode==c)&(Mv.MovementType=="Sale")].QtyChange.sum() for c in P.ItemCode],
 "AdjQty":[Mv[(Mv.ItemCode==c)&(Mv.MovementType=="Adjustment")].QtyChange.sum() for c in P.ItemCode],
 "ClosingQty":cl.reindex(P.ItemCode).values,"MinStock":P.MinStock,"StdCost":P.Cost})
Inv["StockValue"]=(Inv.ClosingQty*Inv.StdCost).round(2); Inv["LastSaleDate"]=last.reindex(P.ItemCode).values
# receivables & payments
Ri=Sa.groupby(["VoucherNo","VoucherDate","PartyCode"],as_index=False).agg(Taxable=("TaxableValue","sum"),Gst=("GSTAmount","sum"))
Ri["BillAmount"]=(Ri.Taxable+Ri.Gst).round(2); terms=C.set_index("CustomerCode").CreditDays
Ri["DueDate"]=[pd.Timestamp(d)+pd.Timedelta(days=int(terms[c])) for d,c in zip(Ri.VoucherDate,Ri.PartyCode)]
pays=[];paid=[];pn=0;asof=pd.Timestamp("2026-10-31")
for _,r in Ri.iterrows():
    c=r.PartyCode; delay=int(rng.integers(-3,10)); 
    if c in slow: delay=int(rng.integers(35,80))
    p_dt=pd.Timestamp(r.DueDate)+pd.Timedelta(days=delay)
    if c in bad and pd.Timestamp(r.VoucherDate)>pd.Timestamp("2026-03-01"): amt=0
    elif p_dt>asof: amt=0
    else: amt=r.BillAmount if rng.random()>.06 else round(r.BillAmount*rng.uniform(.5,.9),2)
    if amt>0: pn+=1; pays.append([f"RCT{pn:05d}",r.VoucherNo,c,p_dt.date(),round(amt,2),str(rng.choice(["NEFT","UPI","Cheque","RTGS"])),"INR"])
    paid.append(round(amt,2))
Ri["PaidAmount"]=paid; Ri["Outstanding"]=(Ri.BillAmount-Ri.PaidAmount).round(2)
Rec=Ri[["VoucherNo","VoucherDate","PartyCode","DueDate","BillAmount","PaidAmount","Outstanding"]].copy(); Rec["Currency"]="INR"; Rec["CreditDays"]=Rec.PartyCode.map(terms)
Pay=pd.DataFrame(pays,columns=["ReceiptNo","BillNo","PartyCode","ReceiptDate","Amount","Mode","Currency"])
# expenses (~11-13% of sales): salaries, rent, freight, etc.
exp=[]; rev_m=Sa.groupby("m").TaxableValue.sum()
for m in months:
    rv=rev_m[m]; eom=m.end_time.date()
    for cat,fix,pct,vend in [("Salaries & Wages",.0,.035,"Payroll"),("Godown Rent",.0,.0,"Landlord"),("Freight & Cartage",.0,.018,"Transporter"),("Electricity & Utilities",0,0,"MSEDCL"),("Marketing & Schemes",0,.008,"Agency"),("Bank Charges & Interest",0,.006,"Bank"),("Repairs & Maintenance",0,.003,"Vendor"),("Office & Admin",0,.004,"Vendor")]:
        amt={"Godown Rent":185000,"Electricity & Utilities":float(rng.integers(34000,46000))}.get(cat, rv*pct*float(rng.uniform(.95,1.05)))
        exp.append([f"EXP/{m.strftime('%y%m')}/{cat[:3].upper()}",eom,cat,vend,round(amt,2),"INR"])
E_=pd.DataFrame(exp,columns=["VoucherNo","VoucherDate","ExpenseHead","Payee","Amount","Currency"])
with pd.ExcelWriter("indian_distributor_demo.xlsx") as w:
    pd.DataFrame({"Item":["Entity","Currency","Reporting cut-off","Note"],"Detail":["Fictional FMCG distributor, Maharashtra, India - synthetic, not a real company","INR (taxable value excludes GST)","2026-10-31","Synthetic data for testing only. Tally/Busy-style headers."]}).to_excel(w,"ReadMe",index=False)
    P.rename(columns={}).to_excel(w,"Item Master",index=False); C.to_excel(w,"Customers",index=False); S.to_excel(w,"Suppliers",index=False)
    Sa.drop(columns="m").to_excel(w,"Sales",index=False); Pu.to_excel(w,"Purchases",index=False); E_.to_excel(w,"Expenses",index=False)
    Mv.to_excel(w,"Stock Movements",index=False); Inv.to_excel(w,"Stock Summary",index=False); Rec.to_excel(w,"Receivables",index=False); Pay.to_excel(w,"Receipts",index=False)
print({k:len(v) for k,v in dict(sales=Sa,purch=Pu,exp=E_,mov=Mv,inv=Inv,rec=Rec,pay=Pay).items()}); print("negatives",(Inv.ClosingQty<0).sum(),"below min",(Inv.ClosingQty<Inv.MinStock).sum())
print("rev",Sa.TaxableValue.sum().round(2),"exp",E_.Amount.sum().round(2),"AR",Rec.Outstanding.sum().round(2))
