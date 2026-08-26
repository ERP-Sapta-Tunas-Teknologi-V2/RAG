const form=document.getElementById("chat-form");
const input=document.getElementById("question");
const messages=document.getElementById("messages");

function addMessage(text,type){
    const el=document.createElement("div");
    el.className=`message ${type}`;
    el.textContent=text;
    messages.appendChild(el);
    messages.scrollTop=messages.scrollHeight;
    return el;
}

form.addEventListener("submit",async e=>{
    e.preventDefault();

    const question=input.value.trim();
    if(!question)return;

    addMessage(question,"user");
    input.value="";
    input.disabled=true;

    const bot=addMessage("Mengetik...","bot");

    try{
        const response=await fetch("/api/chat",{
            method:"POST",
            headers:{"Content-Type":"application/json"},
            body:JSON.stringify({question})
        });

        if(!response.ok){
            const error=await response.json();
            bot.textContent=error.error||"Terjadi kesalahan.";
            return;
        }

        const contentType=response.headers.get("content-type")||"";

        // Fallback JSON
        if(contentType.includes("application/json")){
            const data=await response.json();
            bot.textContent=data.answer;
            return;
        }

        const reader=response.body.getReader();
        const decoder=new TextDecoder();
        let buffer="";
        let answer="";
        let sources=[];

        while(true){
            const {value,done}=await reader.read();
            if(done)break;

            buffer+=decoder.decode(value,{stream:true});

            const events=buffer.split("\n\n");
            buffer=events.pop();

            for(const event of events){
                if(!event.startsWith("data: "))continue;

                const data=JSON.parse(event.slice(6));

                if(data.type==="metadata"){
                    sources=data.sources||[];
                    bot.textContent="";
                }

                if(data.type==="token"){
                    answer+=data.content;
                    bot.textContent=answer;
                    messages.scrollTop=messages.scrollHeight;
                }

                if(data.type==="done"){
                    if(sources.length){
                        const sourceEl=document.createElement("div");
                        sourceEl.className="sources";
                        sourceEl.innerHTML="<b>Sumber:</b>";

                        sources.slice(0,3).forEach(source=>{
                            const link=document.createElement("div");
                            link.textContent=source.source||"Dokumen";
                            sourceEl.appendChild(link);
                        });

                        bot.appendChild(sourceEl);
                    }
                }
            }
        }
    }catch(error){
        bot.textContent="Terjadi kesalahan saat menghubungi server.";
        console.error(error);
    }finally{
        input.disabled=false;
        input.focus();
    }
});