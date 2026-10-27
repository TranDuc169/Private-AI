// Chrome UI test with mocked API. Start Vite on port 5174.
const {chromium}=require('playwright'),assert=require('node:assert/strict'),fs=require('node:fs');
(async()=>{const browser=await chromium.launch({channel:'chrome',headless:true});try{
 const page=await browser.newPage({viewport:{width:1440,height:1050}});page.setDefaultTimeout(15000);
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 const source={source_id:1,chunk_id:'ch1',document_id:'d1',filename:'02-sql-join.pdf',page_number:1,chunk_index:0,score:0,text:'INNER JOIN giữ hàng khớp; LEFT JOIN giữ mọi hàng bên trái.'};
 let exists=false,pending,delay=false;
 let plan={id:'p1',workspace_id:'w1',status:'draft',revision:0,progress:{relations:false,sql:false},spec:{request:{sessions:4,minutes_per_session:45},planned_minutes:120,budget_minutes:180,assumptions:'Mức nền do người học tự khai.',limitations:'Checklist là tự báo cáo, không phải chấm năng lực.',sources:[source],steps:[{key:'relations',title:'Quan hệ và ràng buộc',minutes:60,prerequisites:[],objective:'Hiểu khóa chính và khóa ngoại.',activity:'Đọc tài liệu và mô tả một ví dụ.',schedule:[{session:1,minutes:45},{session:2,minutes:15}],source_ids:[1]},{key:'sql',title:'SQL và JOIN',minutes:60,prerequisites:['relations'],objective:'Phân biệt INNER JOIN và LEFT JOIN.',activity:'Viết ví dụ JOIN trên giấy rồi đối chiếu.',schedule:[{session:2,minutes:30},{session:3,minutes:30}],source_ids:[1]}]}};
 const result={kind:'roadmap',roadmap_id:'p1',conversation_id:'c1',revision:1,status:'answered',answer:'Đã tạo bản nháp lộ trình có nguồn.',sources:[source],model:'qwen3',elapsed_ms:1000};
 await page.route('http://127.0.0.1:8000/**',async route=>{
  const req=route.request(),path=new URL(req.url()).pathname;
  const reply=(x,status=200)=>route.fulfill({status,contentType:'application/json',headers:{'Access-Control-Allow-Origin':'*'},body:JSON.stringify(x)});
  if(req.method()==='OPTIONS')return route.fulfill({status:204,headers:{'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'*','Access-Control-Allow-Methods':'*'}});
  if(path==='/health')return reply({status:'ok',database:'up'});
  if(path==='/auth/login')return reply({access_token:'mock',expires_in:1800,user:{email:'test@example.com'}});
  if(path==='/workspaces')return reply([{id:'w1',name:'CSDL Demo'},{id:'w2',name:'Workspace khác'}]);
  if(path==='/workspaces/w1/chat'){exists=true;return reply(result);}
  if(path==='/workspaces/w1/conversations')return reply(exists?[{id:'c1',title:'Roadmap SQL JOIN',created_at:'2026-10-27T12:00:00Z'}]:[]);
  if(path==='/workspaces/w2/conversations')return reply([]);
  if(path==='/workspaces/w1/conversations/c1')return reply({id:'c1',revision:1,messages:[{id:'u1',role:'user',content:'Roadmap SQL JOIN; mới bắt đầu; 4 buổi; 45 phút/buổi'},{id:'a1',role:'assistant',content:result.answer,result}]});
  if(path==='/workspaces/w1/plans/p1' && req.method()==='GET')return reply(plan);
  if(path==='/workspaces/w1/plans/p1/confirm'){assert.equal(req.postDataJSON().revision,plan.revision);plan={...plan,status:'confirmed',revision:plan.revision+1};return reply(plan);}
  if(path.includes('/plans/p1/steps/')){const body=req.postDataJSON();assert.equal(body.revision,plan.revision);const key=path.split('/').at(-1);plan={...plan,revision:plan.revision+1,progress:{...plan.progress,[key]:body.done}};if(delay){pending=()=>reply(plan).catch(()=>{});return;}return reply(plan);}
  if(path.endsWith('/sources/ch1'))return reply(source);
  return reply({detail:'Missing'},404);
 });
 async function login(){await page.getByLabel('Email',{exact:true}).fill('test@example.com');await page.getByLabel('Mật khẩu',{exact:true}).fill('password123');await page.getByRole('button',{name:'Đăng nhập',exact:true}).click();await page.getByLabel('Chọn workspace').selectOption('w1');}
 await page.goto('http://127.0.0.1:5174');await login();await page.getByLabel('Câu hỏi Cơ sở dữ liệu',{exact:true}).fill('Roadmap SQL JOIN; mới bắt đầu; 4 buổi; 45 phút/buổi');await page.getByRole('button',{name:'Gửi ↑',exact:true}).click();
 const check=page.getByRole('checkbox',{name:'Tôi đã hoàn thành bước 1',exact:true});await check.waitFor();assert(await check.isDisabled());
 await page.getByRole('button',{name:'Xác nhận kế hoạch này',exact:true}).click();await page.getByRole('heading',{name:'Kế hoạch đã xác nhận',exact:true}).waitFor();await check.click();await page.getByText('1/2 bước tự đánh dấu hoàn thành',{exact:true}).waitFor();
 await page.screenshot({path:__dirname+'/01-roadmap-mocked.png',fullPage:true});
 await page.reload();await login();await page.getByRole('link',{name:'Lịch sử hội thoại',exact:true}).click();await page.getByRole('link',{name:'Roadmap SQL JOIN',exact:true}).click();await check.waitFor();assert(await check.isChecked());
 await check.click();await page.getByText('0/2 bước tự đánh dấu hoàn thành',{exact:true}).waitFor();
 await page.setViewportSize({width:390,height:844});await page.screenshot({path:__dirname+'/02-roadmap-mobile-mocked.png',fullPage:true});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
 delay=true;await check.click();await page.getByLabel('Chọn workspace').selectOption('w2');if(pending)await pending();assert.equal(await page.locator('.plan-card').count(),0);assert.deepEqual(errors,[]);
 fs.writeFileSync(__dirname+'/browser-checks.txt','PASS Chrome with MOCK API: draft disables checklist; confirm; check; reload/login/history retains progress; uncheck saves; mobile no overflow; workspace switch ignores late plan mutation response; no JS errors.\n');console.log('PASS week9 browser mocked');
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exit(1)});


