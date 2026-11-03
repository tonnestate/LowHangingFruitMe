// Illustration only. Customer claims and real fees are NEVER calculated in browser.
export function feePreview(input) {
  if(typeof input!=="string" || !/^\d{1,12}(?:[.,]\d{1,2})?$/.test(input))return null;
  const [euros,cent=""] = input.replace(",",".").split(".");
  const value=BigInt(euros)*100n+BigInt((cent+"00").slice(0,2));
  const fee=(value*3n+50n)/100n; // exact 3% cents, half-up
  const format=n=>{
    const v=n/100n,c=n%100n;
    return v.toString().replace(/\B(?=(\d{3})+(?!\d))/g,".")+","+c.toString().padStart(2,"0")+" €";
  };
  return {input:format(value),fee:format(fee),customer:format(value-fee)};
}
