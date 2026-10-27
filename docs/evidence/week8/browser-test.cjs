// API responses are mocked. Run frontend on 5174; requires Playwright and Chrome.
const {chromium}=require('playwright');
const fs=require('node:fs'),assert=require('node:assert/strict');
(async()=>{ const browser=await chromium.launch({headless:true,channel:'chrome'});
try {
 const page=await browser.newPage({viewport:{width:1440,height:1000}}); page.setDefaultTimeout(15000);
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 let revision=0, messages=[], delayed=false, pending, sourceDeleted=false;
 const source={source_id:1,chunk_id:'chunk1',document_id:'doc1',filename:'04-transaction.pdf',page_number:1,chunk_index:0,score:0.8,text:'BEGIN bắt đầu; COMMIT ghi nhận; ROLLBACK hủy giao dịch.'};
 const answer={workspace_id:'w1',conversation_id:'conv1',kind:'summary',question:'Tóm tắt transaction',status:'answered',answer:'- COMMIT ghi nhận giao dịch. [1]\n- ROLLBACK hủy giao dịch. [1]',sources:[source],model:'qwen3',elapsed_ms:2000,coverage:{topic:'Transaction',selected_chunks:2,matched_chunks:2,selected_pages:2,partial:false,limitation:'Bản tóm tắt dựa trên các đoạn đã chọn.',unavailable_documents:0}};
 await page.route('http://127.0.0.1:8000/**',async route=>{
  const req=route.request(),path=new URL(req.url()).pathname;
  const reply=(body,status=200)=>route.fulfill({status,contentType:'application/json',headers:{'Access-Control-Allow-Origin':'*'},body:JSON.stringify(body)});
  if(req.method()==='OPTIONS')return route.fulfill({status:204,headers:{'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'*','Access-Control-Allow-Methods':'*'}});
  if(path==='/health')return reply({status:'ok',database:'up'});
  if(path==='/auth/login')return reply({access_token:'mock-token',expires_in:1800,user:{email:'test@example.com'}});
  if(path==='/workspaces')return reply([{id:'w1',name:'CSDL Demo'},{id:'w2',name:'Workspace khác'}]);
  if(path.endsWith('/sources/chunk1'))return sourceDeleted?reply({detail:'Đoạn nguồn đã bị xóa.'},404):reply(source);
  if(path==='/workspaces/w1/conversations')return reply(messages.length?[{id:'conv1',title:'Tóm tắt transaction',created_at:'2026-10-27T10:00:00Z'}]:[]);
  if(path==='/workspaces/w2/conversations')return reply([]);
  if(path==='/workspaces/w1/conversations/conv1')return reply({id:'conv1',revision,messages});
  if(path.endsWith('/chat')){
   const body=req.postDataJSON();assert.equal(body.revision,revision);
   const result={...answer,revision:++revision,question:body.question};
   messages.push({id:'u'+revision,role:'user',content:body.question},{id:'a'+revision,role:'assistant',content:result.answer,result});
   if(delayed){pending=()=>reply(result).catch(()=>{});return;}
   return reply(result);
  }
  return reply({detail:'Missing'},404);
 });
 const login=async()=>{await page.getByLabel('Email',{exact:true}).fill('test@example.com');await page.getByLabel('Mật khẩu',{exact:true}).fill('password123');await page.getByRole('button',{name:'Đăng nhập',exact:true}).click();await page.getByLabel('Chọn workspace').selectOption('w1');};
 await page.goto('http://127.0.0.1:5174');await login();
 await page.getByLabel('Câu hỏi Cơ sở dữ liệu',{exact:true}).fill('Tóm tắt transaction');await page.getByRole('button',{name:'Gửi ↑',exact:true}).click();
 await page.waitForURL('**/chat/conv1');await page.locator('.assistant-answer').waitFor();await page.locator('.user-question').waitFor();assert.equal(await page.locator('.user-question').count(),1);
 await page.locator('.retrieval-results summary').click();await page.getByRole('button',{name:'Mở đoạn nguồn hiện tại',exact:true}).click();await page.getByText(source.text,{exact:true}).nth(1).waitFor();
 await page.screenshot({path:__dirname+'/01-history-summary-mocked.png',fullPage:true});
 sourceDeleted=true;await page.getByRole('button',{name:'Mở đoạn nguồn hiện tại',exact:true}).click();await page.getByRole('alert').waitFor();assert(await page.locator('.source-text').first().isVisible());
 await page.reload();await login();await page.getByRole('link',{name:'Lịch sử hội thoại',exact:true}).click();await page.getByRole('link',{name:'Tóm tắt transaction',exact:true}).click();await page.locator('.assistant-answer').waitFor();
 await page.setViewportSize({width:390,height:844});await page.screenshot({path:__dirname+'/02-mobile-mocked.png',fullPage:true});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
 delayed=true;await page.getByLabel('Câu hỏi Cơ sở dữ liệu',{exact:true}).fill('Tóm tắt lại transaction');await page.getByRole('button',{name:'Gửi ↑',exact:true}).click();await page.getByRole('button',{name:'Dừng chờ',exact:true}).waitFor();
 await page.getByLabel('Chọn workspace').selectOption('w2');if(pending)await pending();assert.equal(await page.locator('.assistant-answer').count(),0);await page.getByRole('link',{name:'Lịch sử hội thoại',exact:true}).click();await page.getByText('Chưa có hội thoại. Gửi câu hỏi ở Chat chung để tạo lịch sử.',{exact:true}).waitFor();
 assert.deepEqual(errors,[]);fs.writeFileSync(__dirname+'/browser-checks.txt','PASS mocked API UI: saved navigation; history after reload/login; scope display; current source; deleted-source snapshot; workspace switch ignores late response; mobile no overflow; no JS errors. Not a live model browser test.\n');console.log('PASS week8 mocked browser');
} finally {await browser.close();}})().catch(e=>{console.error(e);process.exit(1)});

