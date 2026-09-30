// Collection only: no email provider, send endpoint, or scheduled sender.
export default {
  async fetch(request, env) {
    const origin = request.headers.get('Origin');
    const allowed = ['https://fedregintel.com', 'https://www.fedregintel.com'];
    const headers = {'Content-Type':'application/json', 'Cache-Control':'no-store', 'Vary':'Origin'};
    if (allowed.includes(origin)) headers['Access-Control-Allow-Origin'] = origin;
    const reply = (status, body) => new Response(JSON.stringify(body), {status, headers});
    if (!allowed.includes(origin)) return reply(403, {error:'Please use the signup form on FedRegIntel.com.'});
    if (new URL(request.url).pathname !== '/signup') return reply(404, {error:'Not found.'});
    if (request.method === 'OPTIONS') return new Response(null, {status:204, headers:{...headers, 'Access-Control-Allow-Methods':'POST', 'Access-Control-Allow-Headers':'Content-Type'}});
    if (request.method !== 'POST') return reply(405, {error:'Method not allowed.'});
    if (!env.DB || !env.TURNSTILE_SECRET) return reply(503, {error:'Signups are temporarily unavailable. Please try again later.'});
    try {
      const raw = await request.text();
      if (raw.length > 4096) return reply(413, {error:'Submission too large.'});
      const body = JSON.parse(raw);
      const email = typeof body.email === 'string' ? body.email.trim().toLowerCase() : '';
      if (body.website) return reply(400, {error:'Please try again.'});
      if (body.consent !== true || email.length > 254 || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return reply(400, {error:'Enter a valid email and agree to receive future updates.'});
      if (typeof body.token !== 'string' || !body.token) return reply(400, {error:'Please complete the security check.'});
      const verification = await fetch('https://challenges.cloudflare.com/turnstile/v0/siteverify', {
        method:'POST', headers:{'Content-Type':'application/json'},
        body:JSON.stringify({secret:env.TURNSTILE_SECRET, response:body.token})
      });
      if (!verification.ok) return reply(503, {error:'Security check unavailable. Please try again later.'});
      const verified = await verification.json();
      if (!verified.success || !['fedregintel.com','www.fedregintel.com'].includes(verified.hostname) || verified.action !== 'signup') return reply(400, {error:'Security check expired or failed. Please try again.'});
      await env.DB.prepare('INSERT INTO subscribers (email, subscribed_at, consent_version, source, status) VALUES (?, ?, ?, ?, ?) ON CONFLICT(email) DO NOTHING')
        .bind(email, new Date().toISOString(), '2026-09-30', 'website-signup', 'pending-launch-unverified').run();
      return reply(200, {message:'Thank you! Your signup has been saved. Emails are currently on hold, so no confirmation email will arrive.'});
    } catch {
      // Do not log submitted addresses or request bodies.
      return reply(503, {error:'We could not save your signup. Please try again later.'});
    }
  }
};
