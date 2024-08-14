import {useState, useCallback} from 'react'
import axios from "axios";


//Sends selected nodes to fastapi for report generation
export const sendReportRequest=async(ids:any)=>{
    console.log(ids.selectedNodes);
    console.log(ids.selectedNodes.join(" "));
    const response=await axios.post(`http://localhost:8000/report?ids=${ids.selectedNodes.join(" ")}`, {
    });
    console.log(response)
      
    
  }

//Sends the prompt for analysis generation
export function useFetchFlow() {
  const [controller, setController] = useState<AbortController | null>(null);

  const startFetching = useCallback(async(data: any, addNode) => {
  console.log(data);
  const newController=new AbortController()
  setController(newController);
  // const signal=newController.signal;
  const fetchData=async()=>{
    try{
      let jsonString:any={};
      let getting_plotly=false;
      const response = await fetch(`http://localhost:8000/api?prompt=${data.textInput}`, {
        method: 'POST',
      });
      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let done = false;
      while (!done) {
        const { value, done: readerDone } = await reader.read();
        done = readerDone;
        if (value) {
          const chunky = decoder.decode(value, {stream: !done});
          const splitData=chunky.split("\n\n\n\n");
          splitData.forEach((chunk)=>{
            console.log(chunk);
            if(chunk.trim()){
              try{
                console.log(getting_plotly)
                if(!getting_plotly){
                  const parsedData = JSON.parse(chunk);
                  console.log(parsedData);
                  console.log(parsedData.content[0].type);
                  if(parsedData.content[0].type==="plotly"){
                    getting_plotly=true;
                    jsonString=parsedData;
                    console.log("waiting for plotly");
                  }
                  else{
                    const newNode = {
                      id: parsedData.content[0].id,
                      data: parsedData,
                      position: { x: Math.random() * 250, y: Math.random() * 250 }, // Positioning new nodes randomly
                      type: 'chatResponse', // Adjust the type based on your needs
                      category: parsedData.content[0].category,
                      connecting: parsedData.content[0].connecting
                    }
        
                    addNode(newNode);
                    jsonString={}
                  }

                }
                else{
                  if(chunk.substring(0,4)==="done"){
                    console.log(jsonString.content[0])
                    jsonString.content[0].content=JSON.parse(jsonString.content[0].content.replace("[object Object]","").replace(/'/g, "\\'"));
                    jsonString.content.push(JSON.parse(chunk.substring(4)).content[0]);
                    const newNode = {
                      id: jsonString.content[0].id,
                      data: jsonString,
                      position: { x: Math.random() * 250, y: Math.random() * 250 }, // Positioning new nodes randomly
                      type: 'chatResponse', // Adjust the type based on your needs
                      category: jsonString.content[0].category,
                      connecting: jsonString.content[0].connecting
                    }
        

        
                    addNode(newNode);
                    jsonString={};
                    getting_plotly=false;
                  }
                  else{
                    jsonString.content[0].content+=chunk.replace("[object Object]","");

                  }
                }

              }
              catch(error){
                console.log(error)
              }
            }
          })
        }

      };
    }catch (error) {
      if (error.name === 'AbortError') {
          // Fetch was aborted
          console.log('Fetch aborted');
      } else {
          console.log("Fetch error:", error);
      }
    }
  
    console.log("exited stream")

    }      
    fetchData();
  },[]);

  const stopFetching = useCallback(() => {
    if (controller) {
        controller.abort();
        setController(null);
    }
  }, [controller]);
  return {startFetching, stopFetching};
}
