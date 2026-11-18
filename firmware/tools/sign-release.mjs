import fs from 'node:fs';
import crypto from 'node:crypto';
const [keyPath, binaryPath, sequence, output]=process.argv.slice(2);
if(!output||!/^\d+$/.test(sequence)||+sequence<=0||+sequence>0xffffffff)throw Error('Usage: node sign-release.mjs private-P256.pem firmware.bin releaseNumber output.twup');
const key=crypto.createPrivateKey(fs.readFileSync(keyPath));
if(key.asymmetricKeyDetails.namedCurve!=='prime256v1')throw Error('Use an owner-controlled P-256 key');
const binary=fs.readFileSync(binaryPath);
if(binary[0]!==0xe9||binary.length>0x300000||binary.readUInt16LE(12)!==9)throw Error('Expected an ESP32-S3 application image that fits one Rev E slot');
const header=Buffer.alloc(52);header.write('TWOTA001');header.writeUInt32LE(0x52454645,8);header.writeUInt32LE(+sequence,12);header.writeUInt32LE(binary.length,16);crypto.createHash('sha256').update(binary).digest().copy(header,20);
const signature=crypto.sign('sha256',header,key),len=Buffer.alloc(2);len.writeUInt16LE(signature.length);
fs.writeFileSync(output,Buffer.concat([header,len,signature,binary]),{flag:'wx'});
console.log('USB public-key provisioning command: api1 trust '+crypto.createPublicKey(key).export({type:'spki',format:'der'}).toString('hex'));

