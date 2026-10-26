// Reproduce with Playwright installed or NODE_PATH pointing to its package directory.
// Start the frontend on 127.0.0.1:5174 first. All API calls below are mocked.
const {chromium}=require('playwright');
const fs=require('node:fs'),assert=require('node:assert/strict');
const evidence=__dirname+'/';
(async()=>{const browser=await chromium.launch({headless:true,channel:'chrome'});
try{const page=await browser.newPage({viewport:{width:1440,height:1050}});page.setDefaultTimeout(60000);
const errors=[];page.on('pageerror',e=>errors.push(e.message));
let mode='ok',pending;
const sample={workspace_id:'ws1',question:'Khóa chính là gì?',status:'answered',answer:'Khóa chính định danh mỗi hàng, có giá trị duy nhất và không NULL. [1]',sources:[{source_id:1,chunk_id:'c1',document_id:'d1',filename:'01-quan-he-rang-buoc.pdf',page_number:1,chunk_index:0,score:0.8,text:'PRIMARY KEY (khóa chính) định danh mỗi hàng: giá trị phải duy nhất và không NULL.'}],model:'qwen3:4b-instruct-2507-q4_K_M',elapsed_ms:1000};
await page.route('http://127.0.0.1:8000/**',async route=>{
const req=route.request(),path=new URL(req.url()).pathname;
const reply=(body,status=200)=>route.fulfill({status,contentType:'application/json',headers:{'Access-Control-Allow-Origin':'*'},body:JSON.stringify(body)});
if(req.method()==='OPTIONS')return route.fulfill({status:204,headers:{'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'*','Access-Control-Allow-Methods':'GET,POST,PATCH,DELETE'}});
if(path==='/health')return reply({status:'ok',database:'up'});
if(path==='/auth/login')return reply({access_token:'ui-test-token',expires_in:1800,user:{email:'demo@example.com'}});
if(path==='/workspaces')return reply([{id:'ws1',name:'CSDL - Demo'},{id:'ws2',name:'Workspace trống'}]);
if(path.endsWith('/chat')){
 assert.deepEqual(Object.keys(req.postDataJSON()),['question']);
 if(mode==='error')return reply({detail:'Không gọi được Qwen. Kiểm tra Ollama đang chạy rồi thử lại.'},503);
 if(mode==='delay'){pending=()=>reply(sample).catch(()=>{});return;}
 if(path.includes('ws2'))return reply({...sample,status:'no_documents',answer:'Workspace chưa có đoạn tài liệu sẵn sàng.',sources:[]});
 if(mode==='unsafe')return reply({...sample,answer:'<img src=x onerror=alert(1)> [1]'});
 return reply(sample);
}
return reply([]);
});
await page.goto('http://127.0.0.1:5174');await page.getByLabel('Email',{exact:true}).fill('demo@example.com');await page.getByLabel('Mật khẩu',{exact:true}).fill('password123');await page.getByRole('button',{name:'Đăng nhập',exact:true}).click();
const send=page.getByRole('button',{name:'Gửi ↑',exact:true}),input=page.getByLabel('Câu hỏi Cơ sở dữ liệu',{exact:true});
await send.waitFor();assert(await send.isDisabled());await page.getByLabel('Chọn workspace').selectOption('ws1');
await input.fill('Khóa chính là gì?');await send.click();await page.locator('.assistant-answer').waitFor();await page.locator('.retrieval-results summary').click();
assert((await page.locator('.source-text').innerText()).includes('PRIMARY KEY'));
await page.screenshot({path:evidence+'01-chat-ui-mocked.png',fullPage:true});
mode='unsafe';await input.fill('Hiển thị văn bản');await send.click();await page.getByText('<img src=x onerror=alert(1)> [1]',{exact:true}).waitFor();assert.equal(await page.locator('.assistant-answer img').count(),0);
mode='error';await input.fill('Thử lỗi');await send.click();await page.getByRole('alert').waitFor();await page.getByRole('button',{name:'Đưa câu hỏi vào ô nhập để thử lại'}).click();assert.equal(await input.inputValue(),'Thử lỗi');
mode='delay';await send.click();await page.getByRole('button',{name:'Dừng chờ',exact:true}).waitFor();await page.getByLabel('Chọn workspace').selectOption('ws2');if(pending)await pending();assert.equal(await page.locator('.assistant-answer').count(),0);
mode='ok';await input.fill('Câu hỏi');await send.click();await page.getByText('Workspace chưa có đoạn tài liệu sẵn sàng.',{exact:true}).waitFor();assert.equal(await page.locator('.retrieval-results li').count(),0);
await page.getByLabel('Chọn workspace').selectOption('ws1');await input.fill('Khóa chính là gì?');await send.click();await page.locator('.assistant-answer').waitFor();await page.setViewportSize({width:390,height:844});await page.screenshot({path:evidence+'02-mobile-ui-mocked.png',fullPage:true});
assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));assert.deepEqual(errors,[]);
fs.writeFileSync(evidence+'browser-tests.txt','PASS: Chrome UI with MOCKED API responses. No workspace disabled; answer/source display; HTML escaped; 503 and retry draft; workspace switch cancels stale results; empty workspace; mobile no horizontal overflow; no JS errors. This does NOT verify a live database/model pipeline.\n');
console.log('PASS browser UI (mocked API)');
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exit(1)});
