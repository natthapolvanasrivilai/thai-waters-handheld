// Orthographic triangle rasterizer for browsers that deny WebGL in a downloaded handbook.
import {Matrix4,Vector3} from 'three';

export function softwareRenderer(canvas){
  const ctx=canvas.getContext('2d');
  let image,depth;
  function setSize(w,h){
    const scale=Math.min(1,840/w,680/h);
    canvas.width=Math.max(1,Math.round(w*scale));
    canvas.height=Math.max(1,Math.round(h*scale));
    image=ctx.createImageData(canvas.width,canvas.height);
    depth=new Float32Array(canvas.width*canvas.height);
  }
  function render(scene,camera){
    if(!image)return;
    camera.updateMatrixWorld();scene.updateMatrixWorld();
    const w=canvas.width,h=canvas.height,data=image.data;
    data.fill(0);depth.fill(Infinity);
    const projection=new Matrix4().multiplyMatrices(camera.projectionMatrix,camera.matrixWorldInverse);
    function drawMesh(mesh){
      const g=mesh.geometry, xyz=g.attributes.position.array, indices=g.index.array;
      const mat=mesh.material, matrix=new Matrix4().multiplyMatrices(projection,mesh.matrixWorld).elements;
      const pos=new Float32Array(xyz.length);
      for(let i=0;i<xyz.length;i+=3){
        const x=xyz[i],y=xyz[i+1],z=xyz[i+2];
        pos[i]=(1+matrix[0]*x+matrix[4]*y+matrix[8]*z+matrix[12])*w*.5;
        pos[i+1]=(1-matrix[1]*x-matrix[5]*y-matrix[9]*z-matrix[13])*h*.5;
        pos[i+2]=matrix[2]*x+matrix[6]*y+matrix[10]*z+matrix[14];
      }
      const color=mat.color.getHex(),r=color>>16,b=color&255,green=color>>8&255;
      for(let i=0;i<indices.length;i+=3){
        const a=indices[i]*3,j=indices[i+1]*3,k=indices[i+2]*3;
        const x=pos[a],y=pos[a+1],ux=pos[j]-x,uy=pos[j+1]-y,vx=pos[k]-x,vy=pos[k+1]-y;
        const det=ux*vy-uy*vx;
        // Outward-wound triangles facing the orthographic camera have negative screen area.
        if(det>-.012)continue;
        const xmin=Math.max(0,Math.floor(Math.min(x,x+ux,x+vx))),xmax=Math.min(w-1,Math.ceil(Math.max(x,x+ux,x+vx)));
        const ymin=Math.max(0,Math.floor(Math.min(y,y+uy,y+vy))),ymax=Math.min(h-1,Math.ceil(Math.max(y,y+uy,y+vy)));
        const ax=xyz[j]-xyz[a],ay=xyz[j+1]-xyz[a+1],az=xyz[j+2]-xyz[a+2];
        const bx=xyz[k]-xyz[a],by=xyz[k+1]-xyz[a+1],bz=xyz[k+2]-xyz[a+2];
        const nx=ay*bz-az*by,ny=az*bx-ax*bz,nz=ax*by-ay*bx;
        const brightness=.78+.26*(nx*.36-ny*.5+nz*.79)/(Math.hypot(nx,ny,nz)||1);
        for(let py=ymin;py<=ymax;py++)for(let px=xmin;px<=xmax;px++){
          const dx=px+.5-x,dy=py+.5-y;
          const u=(dx*vy-dy*vx)/det,v=(ux*dy-uy*dx)/det;
          if(u<0||v<0||u+v>1)continue;
          const z=pos[a+2]+u*(pos[j+2]-pos[a+2])+v*(pos[k+2]-pos[a+2]), p=py*w+px;
          if(z>=depth[p])continue;
          const n=p*4,alpha=mat.opacity,back=data[n+3]/255,combined=alpha+back*(1-alpha);
          for(const [channel,value] of [[0,r],[1,green],[2,b]]){
            data[n+channel]=(brightness*value*alpha+data[n+channel]*back*(1-alpha))/combined;
          }
          data[n+3]=255*combined;if(alpha===1)depth[p]=z;
        }
      }
    }
    const meshes=scene.children.filter(m=>m.isMesh&&m.visible);
    meshes.sort((a,b)=>a.renderOrder-b.renderOrder).forEach(drawMesh);
    ctx.putImageData(image,0,0);
    ctx.strokeStyle='#946c3d';ctx.setLineDash([4,3]);
    for(const line of scene.children.filter(o=>o.isLine&&o.visible)){
      const attr=line.geometry.attributes.position,pt=new Vector3();ctx.beginPath();
      for(let i=0;i<attr.count;i++){
        pt.fromBufferAttribute(attr,i).project(camera);
        const x=(pt.x+1)*w*.5,y=(1-pt.y)*h*.5;
        if(i===0)ctx.moveTo(x,y);else ctx.lineTo(x,y);
      }
      ctx.stroke();
    }
  }
  return {domElement:canvas,setSize,render};
}
