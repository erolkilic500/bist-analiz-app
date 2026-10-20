//@version=5
strategy("Tek Kademe Scalping - Canli Tablo", overlay=true, initial_capital=100000, default_qty_type=strategy.cash, default_qty_value=1000)

p1_offset = input.float(0.2, "Alış (Fiyattan % Kaç Altta?)", step=0.1)
p1_tp_quick = input.float(1.5, "1. Hızlı Kâr Al (%1.5)", step=0.1)
p1_tp_main = input.float(3.0, "2. Ana Kâr Al (%3.0)", step=0.1)
p1_sl = input.float(1.5, "Sabit Stop Loss (%1.5)", step=0.1)
closeSession = input.bool(true, "17:55 Otomatik Kapat")

[macdLine, signalLine, _] = ta.macd(close, 12, 26, 9)
cond_macd = macdLine > signalLine

ema1 = ta.ema(close, 9)
ema2 = ta.ema(ema1, 9)
ema3 = ta.ema(ema2, 9)
tema = 3 * (ema1 - ema2) + ema3
cond_tema = close > tema

ema20 = ta.ema(close, 20)
ema50 = ta.ema(close, 50)
cond_ema = ema20 > ema50

volSMA = ta.sma(volume, 20)
cond_vol = volume > volSMA

obvVal = ta.cum(math.sign(ta.change(close)) * volume)
obvSMA = ta.sma(obvVal, 10)
cond_obv = obvVal > obvSMA

rsiVal = ta.rsi(close, 14)
stochK = ta.sma(ta.stoch(rsiVal, rsiVal, rsiVal, 14), 3)
stochD = ta.sma(stochK, 3)
cond_stoch = stochK > stochD

atrVal = ta.atr(14)
cond_atr = (high - low) > (atrVal * 0.5)

[bbBasis, bbUpper, bbLower] = ta.bb(close, 20, 2)
cond_bb = close > bbLower and close < bbUpper

int buyScore = (cond_macd ? 1 : 0) + (cond_tema ? 1 : 0) + (cond_ema ? 1 : 0) + (cond_vol ? 1 : 0) + (cond_obv ? 1 : 0) + (cond_stoch ? 1 : 0) + (cond_atr ? 1 : 0) + (cond_bb ? 1 : 0)
bool isBuySignal = buyScore >= 5
isEndOfDay = closeSession and (hour == 17 and minute >= 55)

var float activeBasePrice = na
if strategy.position_size == 0 or math.abs(activeBasePrice - hlc3) / hlc3 > 0.10
    activeBasePrice := hlc3

buyPrice1 = activeBasePrice * (1 - p1_offset / 100)
tp1_quick = buyPrice1 * (1 + p1_tp_quick / 100)
tp1_main = buyPrice1 * (1 + p1_tp_main / 100)
sl1 = buyPrice1 * (1 - p1_sl / 100)

if isEndOfDay
    strategy.close_all(comment="Seans Kapanis")
    strategy.cancel_all()
else
    if (ta.crossunder(low, buyPrice1) or (isBuySignal and low <= buyPrice1)) and strategy.position_size == 0
        strategy.entry("K1", strategy.long, limit=buyPrice1)
    if strategy.position_size > 0 and strategy.opentrades.entry_id(0) == "K1"
        strategy.exit("TP1_Kar", "K1", qty_percent=50, limit=tp1_quick, stop=sl1)
        strategy.exit("TP2_Kar", "K1", limit=tp1_main, stop=sl1)

cCyan = #00FFFF
cLime = #00FF00
cRed = #FF2A2A
cWhite = #FFFFFF
cTrans = color.new(color.black, 100) 
cBlack = #000000FF 
cOffWhite = #EAECEF 
cBrightGreen = #008000 
cBrightRed   = #D32F2F 

plot(buyPrice1, "Alis", color=cCyan, style=plot.style_linebr)
plot(tp1_quick, "TP1", color=color.yellow, style=plot.style_linebr)
plot(tp1_main, "TP2", color=cLime, style=plot.style_linebr)

m1_min = low
m1_max = high
m1_avg = hlc3

m5_min = request.security(syminfo.tickerid, "5", low)
m5_max = request.security(syminfo.tickerid, "5", high)
m5_avg = request.security(syminfo.tickerid, "5", hlc3)

var float day_min = high
var float day_max = low
var float day_avg = hlc3

bool isNewDay = ta.change(time("D")) != 0
if isNewDay
    day_min := low
    day_max := high
    day_avg := hlc3
else
    day_min := math.min(day_min, low)
    day_max := math.max(day_max, high)
    day_avg := (day_min + day_max) / 2

int trTime = timenow + (3 * 3600 * 1000)
int curH = hour(trTime, "UTC")
int curM = minute(trTime, "UTC")
string localTimeStr = (curH < 10 ? "0" : "") + str.tostring(curH) + ":" + (curM < 10 ? "0" : "") + str.tostring(curM)
string barTimeStr = (hour < 10 ? "0" : "") + str.tostring(hour) + ":" + (minute < 10 ? "0" : "") + str.tostring(minute)

var table t = table.new(position.top_right, 4, 14, cTrans, border_width=1, border_color=cWhite)

if barstate.islast
    for int i = 0 to 3
        table.cell(t, i, 0, "", bgcolor=cTrans, text_color=cTrans)
        table.cell(t, i, 1, "", bgcolor=cTrans, text_color=cTrans)

    table.cell(t, 0, 2, text=localTimeStr, bgcolor=cBlack, text_color=cWhite, text_size=size.small)
    table.cell(t, 1, 2, text="Alis", bgcolor=cBlack, text_color=cWhite, text_size=size.small)
    table.cell(t, 2, 2, text="TP", bgcolor=cBlack, text_color=cWhite, text_size=size.small)
    table.cell(t, 3, 2, text="Stop", bgcolor=cBlack, text_color=cWhite, text_size=size.small)

    string tpText = str.tostring(tp1_quick, "#.##") + "/" + str.tostring(tp1_main, "#.##")
    table.cell(t, 0, 3, text=barTimeStr, bgcolor=cBlack, text_color=cWhite, text_size=size.small)
    table.cell(t, 1, 3, text=str.tostring(buyPrice1, "#.##"), bgcolor=cBlack, text_color=cCyan, text_size=size.small)
    table.cell(t, 2, 3, text=tpText, bgcolor=cBlack, text_color=cLime, text_size=size.small)
    table.cell(t, 3, 3, text=str.tostring(sl1, "#.##"), bgcolor=cBlack, text_color=cRed, text_size=size.small)

    table.cell(t, 0, 5, text="Periyot", bgcolor=cBlack, text_color=cWhite, text_size=size.small)
    table.cell(t, 1, 5, text="Min", bgcolor=cBlack, text_color=cWhite, text_size=size.small)
    table.cell(t, 2, 5, text="Ort", bgcolor=cBlack, text_color=cWhite, text_size=size.small)
    table.cell(t, 3, 5, text="Max", bgcolor=cBlack, text_color=cWhite, text_size=size.small)

    table.cell(t, 0, 6, text="1D", bgcolor=cBlack, text_color=cWhite, text_size=size.small)
    table.cell(t, 1, 6, text=str.tostring(m1_min, "#.##"), bgcolor=cBlack, text_color=cRed, text_size=size.small)
    table.cell(t, 2, 6, text=str.tostring(m1_avg, "#.##"), bgcolor=cBlack, text_color=cCyan, text_size=size.small)
    table.cell(t, 3, 6, text=str.tostring(m1_max, "#.##"), bgcolor=cBlack, text_color=cLime, text_size=size.small)

    table.cell(t, 0, 7, text="5D", bgcolor=cBlack, text_color=cWhite, text_size=size.small)
    table.cell(t, 1, 7, text=str.tostring(m5_min, "#.##"), bgcolor=cBlack, text_color=cRed, text_size=size.small)
    table.cell(t, 2, 7, text=str.tostring(m5_avg, "#.##"), bgcolor=cBlack, text_color=cCyan, text_size=size.small)
    table.cell(t, 3, 7, text=str.tostring(m5_max, "#.##"), bgcolor=cBlack, text_color=cLime, text_size=size.small)

    table.cell(t, 0, 8, text="Gun", bgcolor=cBlack, text_color=cWhite, text_size=size.small)
    table.cell(t, 1, 8, text=str.tostring(day_min, "#.##"), bgcolor=cBlack, text_color=cRed, text_size=size.small)
    table.cell(t, 2, 8, text=str.tostring(day_avg, "#.##"), bgcolor=cBlack, text_color=cCyan, text_size=size.small)
    table.cell(t, 3, 8, text=str.tostring(day_max, "#.##"), bgcolor=cBlack, text_color=cLime, text_size=size.small)

    cM = cond_macd ? cBrightGreen : cBrightRed
    cT = cond_tema ? cBrightGreen : cBrightRed
    cE = cond_ema  ? cBrightGreen : cBrightRed
    cV = cond_vol  ? cBrightGreen : cBrightRed
    cO = cond_obv  ? cBrightGreen : cBrightRed
    cS = cond_stoch ? cBrightGreen : cBrightRed
    cA = cond_atr  ? cBrightGreen : cBrightRed
    cB = cond_bb   ? cBrightGreen : cBrightRed

    table.cell(t, 0, 9, text="MACD", bgcolor=cOffWhite, text_color=cM, text_size=size.small)
    table.cell(t, 1, 9, text=cond_macd ? "[ + ]" : "[ - ]", bgcolor=cOffWhite, text_color=cM, text_size=size.small)
    table.cell(t, 2, 9, text="TEMA", bgcolor=cOffWhite, text_color=cT, text_size=size.small)
    table.cell(t, 3, 9, text=cond_tema ? "[ + ]" : "[ - ]", bgcolor=cOffWhite, text_color=cT, text_size=size.small)

    table.cell(t, 0, 10, text="EMA 20/50", bgcolor=cOffWhite, text_color=cE, text_size=size.small)
    table.cell(t, 1, 10, text=cond_ema ? "[ + ]" : "[ - ]", bgcolor=cOffWhite, text_color=cE, text_size=size.small)
    table.cell(t, 2, 10, text="Hacim", bgcolor=cOffWhite, text_color=cV, text_size=size.small)
    table.cell(t, 3, 10, text=cond_vol ? "[ + ]" : "[ - ]", bgcolor=cOffWhite, text_color=cV, text_size=size.small)

    table.cell(t, 0, 11, text="OBV", bgcolor=cOffWhite, text_color=cO, text_size=size.small)
    table.cell(t, 1, 11, text=cond_obv ? "[ + ]" : "[ - ]", bgcolor=cOffWhite, text_color=cO, text_size=size.small)
    table.cell(t, 2, 11, text="Stoch", bgcolor=cOffWhite, text_color=cS, text_size=size.small)
    table.cell(t, 3, 11, text=cond_stoch ? "[ + ]" : "[ - ]", bgcolor=cOffWhite, text_color=cS, text_size=size.small)

    table.cell(t, 0, 12, text="ATR", bgcolor=cOffWhite, text_color=cA, text_size=size.small)
    table.cell(t, 1, 12, text=cond_atr ? "[ + ]" : "[ - ]", bgcolor=cOffWhite, text_color=cA, text_size=size.small)
    table.cell(t, 2, 12, text="BB", bgcolor=cOffWhite, text_color=cB, text_size=size.small)
    table.cell(t, 3, 12, text=cond_bb ? "[ + ]" : "[ - ]", bgcolor=cOffWhite, text_color=cB, text_size=size.small)

    sigText = isBuySignal ? "AL" : "BEKLE"
    sigBg = isBuySignal ? color.green : cBlack
    sigTxt = isBuySignal ? cWhite : color.gray
    scoreText = str.tostring(buyScore) + "/8"
    table.cell(t, 0, 13, text="SINYAL", bgcolor=cBlack, text_color=cWhite, text_size=size.small)
    table.cell(t, 1, 13, text=sigText, bgcolor=sigBg, text_color=sigTxt, text_size=size.small)
    table.cell(t, 2, 13, text="Skor:", bgcolor=cBlack, text_color=cWhite, text_size=size.small)
    table.cell(t, 3, 13, text=scoreText, bgcolor=cBlack, text_color=cCyan, text_size=size.small)
