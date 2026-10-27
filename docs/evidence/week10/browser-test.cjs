// UI checks with mocked API; backend authorization is tested separately.
const {chromium}=require('playwright'),assert=require('node:assert/strict'),fs=require('node:fs');
(async()=>{const browser=await chromium.launch({channel:'chrome',headless:true});try{
 const page=await browser.newPage({viewport:{width:1440,height:1050}});page.setDefaultTimeout(15000);
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 const source={source_id:1,chunk_id:'ch1',document_id:'d1',filename:'02-sql-join.pdf',page_number:1,chunk_index:0,score:0,text:'LEFT JOIN giữ mọi hàng bên trái; HAVING lọc nhóm sau GROUP BY.'};
 let exists=false,pending,delay=false,submitted=false,draft=false;
 const feedback=[{correct:2,explanation:'LEFT JOIN giữ hàng trái, cột bên phải NULL.',source_id:1},{correct:3,explanation:'HAVING lọc nhóm sau GROUP BY.',source_id:1}];
 const quiz=()=>({id:'q1',status:draft?'draft':'approved',topic:'SQL và JOIN',review:draft?'AI sinh mới; chưa rà soát.':'Bộ demo đối chiếu phiếu học tập.',questions:[{question:'LEFT JOIN giữ lại hàng nào?',choices:['Chỉ hàng khớp','Không hàng nào','Mọi hàng trái','Tạo hàng phải']},{question:'Mệnh đề nào lọc nhóm?',choices:['WHERE','ON','ORDER BY','HAVING']}],result:submitted?{answers:[2,0],score:1,total:2,feedback,sources:[source]}:null,related_plan:null});
 const result={kind:'quiz',quiz_id:'q1',conversation_id:'c1',revision:1,status:'answered',answer:'Bài luyện tập demo đã sẵn sàng.',sources:[],model:'qwen3',elapsed_ms:100};
 await page.route('http://127.0.0.1:8000/**',async route=>{
  const req=route.request(),path=new URL(req.url()).pathname;
  const reply=(x,status=200)=>route.fulfill({status,contentType:'application/json',headers:{'Access-Control-Allow-Origin':'*'},body:JSON.stringify(x)});
  if(req.method()==='OPTIONS')return route.fulfill({status:204,headers:{'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'*','Access-Control-Allow-Methods':'*'}});
  if(path==='/health')return reply({status:'ok',database:'up'});
  if(path==='/auth/login')return reply({access_token:'mock',expires_in:1800,user:{email:'test@example.com'}});
  if(path==='/workspaces')return reply([{id:'w1',name:'CSDL Demo'},{id:'w2',name:'Workspace khác'}]);
  if(path==='/workspaces/w1/chat'){exists=true;return reply(result);}
  if(path==='/workspaces/w1/conversations')return reply(exists?[{id:'c1',title:'Quiz SQL JOIN',created_at:'2026-10-27T12:00:00Z'}]:[]);
  if(path==='/workspaces/w2/conversations')return reply([]);
  if(path==='/workspaces/w1/conversations/c1')return reply({id:'c1',revision:1,messages:[{id:'u1',role:'user',content:'Quiz SQL JOIN'},{id:'a1',role:'assistant',content:result.answer,result}]});
  if(path==='/workspaces/w1/quizzes/q1')return reply(quiz());
  if(path==='/workspaces/w1/quizzes/q1/submit'){assert.deepEqual(req.postDataJSON(),{answers:[2,0]});submitted=true;if(delay){pending=()=>reply(quiz()).catch(()=>{});return;}return reply(quiz());}
  if(path.endsWith('/sources/ch1'))return reply(source);
  return reply({detail:'Missing'},404);
 });
 async function login(){await page.getByLabel('Email',{exact:true}).fill('test@example.com');await page.getByLabel('Mật khẩu',{exact:true}).fill('password123');await page.getByRole('button',{name:'Đăng nhập',exact:true}).click();await page.getByLabel('Chọn workspace').selectOption('w1');}
 await page.goto('http://127.0.0.1:5174');await login();await page.getByLabel('Câu hỏi Cơ sở dữ liệu',{exact:true}).fill('Quiz SQL JOIN');await page.getByRole('button',{name:'Gửi ↑',exact:true}).click();
 const submit=page.getByRole('button',{name:'Nộp bài',exact:true});await submit.waitFor();assert(await submit.isDisabled());assert.equal(await page.locator('.quiz-feedback').count(),0);
 await page.getByRole('radio',{name:'C. Mọi hàng trái',exact:true}).check();await page.getByRole('radio',{name:'A. WHERE',exact:true}).check();
 await page.screenshot({path:__dirname+'/01-quiz-before-mocked.png',fullPage:true});
 await submit.click();await page.getByText('Kết quả: 1/2 câu đúng.',{exact:true}).waitFor();assert.equal(await page.locator('.quiz-feedback').count(),2);
 await page.screenshot({path:__dirname+'/02-quiz-result-mocked.png',fullPage:true});
 await page.reload();await login();await page.getByRole('link',{name:'Lịch sử hội thoại',exact:true}).click();await page.getByRole('link',{name:'Quiz SQL JOIN',exact:true}).click();await page.getByText('Kết quả: 1/2 câu đúng.',{exact:true}).waitFor();
 await page.setViewportSize({width:390,height:844});await page.screenshot({path:__dirname+'/03-quiz-mobile-mocked.png',fullPage:true});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
 submitted=false;draft=true;await page.getByRole('button',{name:'Tải lại quiz',exact:true}).click();await page.getByText('AI sinh mới; chưa rà soát.',{exact:true}).waitFor();assert.equal(await submit.count(),0);assert(await page.getByRole('radio').first().isDisabled());
 draft=false;await page.getByRole('button',{name:'Tải lại quiz',exact:true}).click();await submit.waitFor();await page.getByRole('radio',{name:'C. Mọi hàng trái',exact:true}).check();await page.getByRole('radio',{name:'A. WHERE',exact:true}).check();delay=true;await submit.click();await page.getByLabel('Chọn workspace').selectOption('w2');if(pending)await pending();assert.equal(await page.locator('.quiz-card').count(),0);assert.deepEqual(errors,[]);
 fs.writeFileSync(__dirname+'/browser-checks.txt','PASS Chrome MOCK API: answers hidden before submit; requires every answer; submits choices only; score/feedback shown; reload/history persists result; draft disabled; mobile no overflow; workspace switch ignores late result; no JS errors.\n');console.log('PASS week10 browser mocked');
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exit(1)});
