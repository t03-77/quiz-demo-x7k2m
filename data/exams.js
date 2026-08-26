// 試験マスタ。フォルダ/ファイルを増やさなくても、ここに追加すれば試験が増える(仕様書§3.0)
// n/min/pass は本番試験の問題数・制限時間(分)・合格スコア。模擬試験モードがこれを再現する
window.EXAMS = [
  {id:"CLF-C02", short:"CLF", name:"Cloud Practitioner",                      level:"基礎",             n:65, min:90,  pass:700},
  {id:"AIF-C01", short:"AIF", name:"AI Practitioner",                        level:"基礎",             n:65, min:90,  pass:700},
  {id:"SAA-C03", short:"SAA", name:"Solutions Architect – Associate",        level:"アソシエイト",     n:65, min:130, pass:720},
  {id:"DVA-C02", short:"DVA", name:"Developer – Associate",                  level:"アソシエイト",     n:65, min:130, pass:720},
  {id:"SOA-C03", short:"SOA", name:"CloudOps Engineer – Associate",          level:"アソシエイト",     n:65, min:130, pass:720},   // 公式ガイドで確認 (2025年改訂版)
  {id:"DEA-C01", short:"DEA", name:"Data Engineer – Associate",              level:"アソシエイト",     n:65, min:130, pass:720},
  {id:"MLA-C01", short:"MLA", name:"ML Engineer – Associate",                level:"アソシエイト",     n:65, min:130, pass:720},
  {id:"SAP-C02", short:"SAP", name:"Solutions Architect – Professional",     level:"プロフェッショナル", n:75, min:180, pass:750},
  {id:"DOP-C02", short:"DOP", name:"DevOps Engineer – Professional",         level:"プロフェッショナル", n:75, min:180, pass:750},
  {id:"AIP-C01", short:"AIP", name:"Generative AI Developer – Professional", level:"プロフェッショナル", n:75, min:180, pass:750},
  {id:"SCS-C03", short:"SCS", name:"Security – Specialty",                   level:"専門",             n:65, min:170, pass:750},
  {id:"ANS-C01", short:"ANS", name:"Advanced Networking – Specialty",        level:"専門",             n:65, min:170, pass:750, retired:"2026-08-27"}
];
