import net from 'node:net';
import process from 'node:process';

function parseArgs(argv) {
  const result = { listenHost: '127.0.0.1', listenPort: 3000, targetHost: '', targetPort: 3000 };
  for (let i = 2; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === '--listen-host') result.listenHost = argv[++i];
    else if (arg === '--listen-port') result.listenPort = Number(argv[++i]);
    else if (arg === '--target-host') result.targetHost = argv[++i];
    else if (arg === '--target-port') result.targetPort = Number(argv[++i]);
  }
  return result;
}

const { listenHost, listenPort, targetHost, targetPort } = parseArgs(process.argv);

if (!targetHost) {
  console.error('Missing --target-host');
  process.exit(1);
}

const server = net.createServer((client) => {
  const upstream = net.createConnection({ host: targetHost, port: targetPort });

  client.on('error', () => upstream.destroy());
  upstream.on('error', (error) => {
    client.destroy(error);
  });

  client.pipe(upstream);
  upstream.pipe(client);
});

server.on('error', (error) => {
  console.error(error.message);
  process.exit(1);
});

server.listen(listenPort, listenHost, () => {
  console.log(`Proxy listening on http://${listenHost}:${listenPort} -> ${targetHost}:${targetPort}`);
});

function shutdown(signal) {
  server.close(() => process.exit(0));
  setTimeout(() => process.exit(0), 1000).unref();
}

process.on('SIGINT', shutdown);
process.on('SIGTERM', shutdown);
