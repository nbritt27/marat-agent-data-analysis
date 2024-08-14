'use client';

import { Suspense} from 'react';
import {useFetchFlow} from '@/lib/data';

import '@xyflow/react/dist/style.css';

import React, {useCallback, useEffect, useState } from "react";
import axios from "axios";
import Flow from "@/components/Flow";

import { useForm } from "react-hook-form";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

import './Chat.css';

export default async function Page() {
  const { startFetching, stopFetching } = useFetchFlow();
  const [elements, setElements] = useState({ nodes: [], edges: [] });
  const [file, setFile] = useState(null);
  const [controller, setController] = useState<AbortController | null>(null);
  const [loadedFile, setLoadedFile]=useState(false);

  
  const addNode = useCallback((newNode) => {
    setElements((prevElements) => {
      const existingNodeIds = prevElements.nodes.map((node) => node.id);
      console.log(newNode.connecting);
      console.log(newNode.id);
      if (!existingNodeIds.includes(newNode.id)) {
        const newEdge={
          "id": `e${newNode.connecting}-${newNode.id}`,
          source: newNode.connecting,
          target: newNode.id,
          sourceHandle: "bottom",
          targetHandle: "top"
        }
        return {
          nodes: [...prevElements.nodes, newNode],

          edges: [...prevElements.edges, newEdge],
        };
      }
      else{
        console.log("found node with matching id");
      }
      return prevElements;
    });
  },[]);


  const { register, handleSubmit, reset, formState: { errors } } = useForm();

  useEffect(() => {
      return () => {
          if (controller) {
              controller.abort();
          }
      };
  }, [controller]);
  const onQuestionSubmit=async(data:any)=>{
    startFetching(data, addNode);
  }
  const onChatSubmit = async (data: any) => {


      const formSessionData = new FormData();
      formSessionData.append('file_input',file);
      const session_response = await axios.post('http://localhost:8000/session_start', formSessionData, {headers: {
        'Content-Type': 'multipart/form-data',
      }});
      if(session_response.data){
        const parsedData=JSON.parse(session_response.data.replace(/'/g, '"'));
        const newNode = {
          id: parsedData.content[0].id,
          data: parsedData,
          position: { x: Math.random() * 250, y: Math.random() * 250 }, // Positioning new nodes randomly
          type: 'chatResponse', // Adjust the type based on your needs
          connecting: parsedData.content[0].connecting
        };
        addNode(newNode);

        setLoadedFile(true);
        // localStorage.setItem("loadedFile", "true");

      reset();
      }
    }


  return (
    <div>
      
      <div className="px-4 lg:px-8 mt-4">
        
        <Suspense fallback={<p>Loading</p>}>
          {!loadedFile&&(
            <form
            onSubmit={
              handleSubmit(onChatSubmit)}
            className="rounded-lg border w-full p-4 px-3 md:px-6 focus-within:shadow-sm grid grid-cols-12 gap-2">
            <Input className="col-span-8 lg:col-span-10" 
            {...register('file')}
            type="file" onChange={(e) => setFile(e.target.files[0])}></Input>
            <Button
            type="submit">
            -&gt;
            </Button>
            </form>
          )}
            
          {loadedFile&&(
            <form 
            className="rounded-lg border w-full p-4 px-3 md:px-6 focus-within:shadow-sm grid grid-cols-12 gap-2"
            onSubmit={handleSubmit(onQuestionSubmit)}>
              
            <Input className="col-span-8 lg:col-span-10"
            id="textInput"
            {...register('textInput')}
            type="text"
            placeholder="Tell me everything...   What are the contributors to higher prices...   Generate a boxplot"/>
              <Button
              type="submit">
              -&gt;
            </Button>
            </form>

          )}

        </Suspense>
        <Suspense fallback={<p>Loading flow</p>}>
          <div className="flowParent">
            <Flow initialElements={elements}/>
          </div>
        </Suspense>

      </div>
    </div>

  );


}