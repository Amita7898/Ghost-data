// Captures the actual application. No synthetic event injection or model calls.
import {chromium,expect} from '@playwright/test';
import {mkdir,writeFile,readFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
const base=process.env.GHOST_DATA_WEB_URL||'http://127.0.0.1:8000';
const out=resolve(process.argv[2]||'../.demo-capture');
await mkdir(out,{recursive:true});
const browser=await chromium.launch({channel:process.env.CI?undefined:'chrome',headless:true});
const page=await browser.newPage({viewport:{width:1440,height:1000},reducedMotion:'reduce'});
const frames=[];
async function frame(name,description){
  await page.screenshot({path:resolve(out,name)});
  frames.push({file:name,description,sha256:createHash('sha256').update(await readFile(resolve(out,name))).digest('hex')});
}
try {
  await page.goto(base);
  await expect(page.getByText('Replay ready · model offline')).toBeVisible();
  await expect(page.getByRole('button',{name:/Prose receipt audit/})).toBeVisible();
  await frame('01-overview.png','Open the local console; choose a genuine recorded investigation.');
  await page.getByRole('button',{name:/Prose receipt audit/}).click();
  await page.getByRole('button',{name:'Show all',exact:true}).click();
  await expect(page.getByText('verified within scope',{exact:true})).toBeVisible();
  await page.locator('.timeline').evaluate(el=>el.scrollTop=0);
  await frame('02-tools.png','Actual recorded model-selected tool requests; replay is explicitly labeled.');
  await page.locator('.event-card.accepted').scrollIntoViewIfNeeded();
  await frame('03-accepted.png','Supported STATE hypothesis accepted by deterministic source checks.');
  await page.locator('.event-card.accepted').getByRole('button',{name:'Inspect supporting source'}).click();
  await expect(page.locator('.source-code')).toContainText('Observed state: ABSENT');
  await frame('04-source.png','Exact original synthetic source and SHA/row provenance.');
  await page.getByRole('button',{name:'Close evidence inspector'}).click();
  await page.getByRole('link',{name:'Evidence',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Observation inventory'})).toBeVisible();
  await frame('05-evidence.png','Evidence inventory and explicitly distinguished source/agent relationships.');
  await page.goto(base);
  await page.getByRole('button',{name:/Conflicting readbacks/}).click();
  await page.getByRole('button',{name:'Show all',exact:true}).click();
  await expect(page.locator('.event-card.rejected')).toHaveCount(2);
  await page.locator('.event-card.rejected').first().scrollIntoViewIfNeeded();
  await frame('06-rejected.png','Genuine rejected proposals; the final audit remains INCONCLUSIVE.');
  await writeFile(resolve(out,'capture.json'),JSON.stringify({mode:'genuine_offline_replay',created_at:new Date().toISOString(),frames,note:'Accelerated navigation through actual saved events; no invented or rewritten event content.'},null,2)+'\n');
} finally {await browser.close();}
