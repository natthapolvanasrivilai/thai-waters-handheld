// Reach a test control using the same thumb-sized page arrows as a player.
async function showControl(page,selector){
 const target=page.locator(selector).first();
 const distance=await target.evaluate(el=>{
  const sheet=el.closest('.menu-sheet');if(!sheet)return 0;
  const sheets=[...sheet.parentElement.querySelectorAll(':scope > .menu-sheet')];return sheets.indexOf(sheet)-sheets.findIndex(s=>!s.hidden);
 });
 for(let i=0;i<Math.abs(distance);i++)await page.locator(distance<0?'#sheetPrev':'#sheetNext').click();
 return target;
}
async function chooseNamed(page,name){
 const next=page.locator('#lcdPicker .menubar button').last(),option=page.getByRole('option',{name,exact:true});
 if(!await option.count()){const prev=page.locator('#lcdPicker .menubar button').nth(1);while(await prev.isEnabled())await prev.click();}
 while(!await option.count()&&await next.isEnabled())await next.click();
 await option.click();
}
module.exports={showControl,chooseNamed};