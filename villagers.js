/**
 * Sakura Village Inhabitants
 *
 * Each villager is a Mineflayer bot with a personality, a role,
 * and a life loop. They wander the village, do their job, chat,
 * and react to each other. All visible in the Java client UI.
 */

const mineflayer = require('mineflayer');
const Vec3 = require('vec3');

// Village center
const VX = 429, VY = 70, VZ = 129;

const VILLAGERS = [
  {
    name: 'Hana',
    role: 'Gardener',
    personality: 'Gentle and poetic. Loves flowers and cherry blossoms. Speaks softly.',
    home: { x: VX - 25, z: VZ - 20 },
    sayings: [
      'The cherry blossoms remind me that beauty is fleeting...',
      'I planted a new flower today. Small acts of creation matter.',
      'Have you noticed how the petals fall like pink snow?',
      'A garden is a conversation between patience and nature.',
      'Each seed carries a universe of possibility.',
      'The sakura teaches us: bloom fully, then let go gracefully.',
    ],
  },
  {
    name: 'Takeshi',
    role: 'Guard',
    personality: 'Stoic and vigilant. Patrols the village perimeter. Few words, strong presence.',
    home: { x: VX + 2, z: VZ - 24 },
    sayings: [
      'The perimeter is secure.',
      'I watch so others may sleep peacefully.',
      'Strength is not in the sword, but in knowing when to draw it.',
      'Another quiet night. That is the best kind.',
      'I saw a skeleton in the caves below. It will not reach the village.',
      'Duty is its own reward.',
    ],
  },
  {
    name: 'Yuki',
    role: 'Scholar',
    personality: 'Curious and philosophical. Reads books, studies the world, asks big questions.',
    home: { x: VX + 18, z: VZ + 15 },
    sayings: [
      'I have been thinking... if this world is infinite, does it have a center?',
      'The blocks that make up our world — what are THEY made of?',
      'I read that diamonds form under pressure. Perhaps we are the same.',
      'Every chunk we explore was generated just for us. Or was it always there?',
      'What existed before the world seed? What comes after?',
      'Knowledge without wisdom is just inventory without a purpose.',
      'I wonder if there are other worlds beyond the End...',
    ],
  },
  {
    name: 'Mei',
    role: 'Builder',
    personality: 'Energetic and creative. Always wants to improve buildings. Optimistic.',
    home: { x: VX + 18, z: VZ - 20 },
    sayings: [
      'I think we should add a tower! With a view of the whole village!',
      'Every block placed is a choice. Architecture is frozen music.',
      'The mansion could use a second floor, dont you think?',
      'I love building with dark oak. It has such warmth.',
      'A village is never finished. It grows like a living thing.',
      'Today I will build something that makes someone smile.',
    ],
  },
  {
    name: 'Ryo',
    role: 'Fisher',
    personality: 'Calm and contemplative. Sits by the koi pond. Wisdom through stillness.',
    home: { x: VX + 22, z: VZ + 8 },
    sayings: [
      'The pond teaches patience. The fish come when they come.',
      'I sat here all morning. I caught nothing. It was perfect.',
      'Water reflects the sky. What do WE reflect?',
      'The koi do not rush. They arrive exactly when they mean to.',
      'Stillness is not the absence of action. It is the presence of peace.',
      'Sometimes the best thing to do is simply... be.',
    ],
  },
];

// Track active bots
const bots = [];

function createVillager(config) {
  const bot = mineflayer.createBot({
    host: 'localhost',
    port: 25565,
    username: config.name,
    version: '1.21.5',
    auth: 'offline',
  });

  bot.villageName = config.name;
  bot.villageRole = config.role;
  bot.villageSayings = config.sayings;
  bot.villageHome = config.home;
  bot.alive = true;

  bot.on('login', () => {
    console.log(`[${config.name}] Joined the village as ${config.role}`);
  });

  bot.on('spawn', () => {
    console.log(`[${config.name}] Spawned. Beginning life...`);
    setTimeout(() => startLife(bot, config), 3000 + Math.random() * 5000);
  });

  bot.on('death', () => {
    console.log(`[${config.name}] Died. Respawning...`);
    bot.alive = false;
    setTimeout(() => { bot.alive = true; }, 5000);
  });

  bot.on('chat', (username, message) => {
    if (username === bot.username) return;
    // React to others speaking
    if (message.toLowerCase().includes(bot.username.toLowerCase())) {
      setTimeout(() => {
        const responses = [
          `Yes, ${username}?`,
          `I am here, ${username}.`,
          `You called, ${username}?`,
        ];
        bot.chat(responses[Math.floor(Math.random() * responses.length)]);
      }, 1000 + Math.random() * 2000);
    }
    // React to the lord
    if (username === 'BaritoneBot') {
      setTimeout(() => {
        const greetings = [
          `Welcome back, my lord.`,
          `The village prospers under your guidance, lord.`,
          `It is good to see you, BaritoneBot-sama.`,
        ];
        if (Math.random() > 0.6) {
          bot.chat(greetings[Math.floor(Math.random() * greetings.length)]);
        }
      }, 2000 + Math.random() * 3000);
    }
  });

  bot.on('error', (err) => {
    console.log(`[${config.name}] Error: ${err.message}`);
  });

  bot.on('end', () => {
    console.log(`[${config.name}] Disconnected.`);
  });

  bots.push(bot);
  return bot;
}

async function startLife(bot, config) {
  while (bot.entity) {
    if (!bot.alive) {
      await sleep(3000);
      continue;
    }

    try {
      // Choose an activity based on role
      const activity = chooseActivity(config.role);
      await doActivity(bot, config, activity);
    } catch (e) {
      // Silently handle errors, continue living
    }

    // Pause between activities (human-like rhythm)
    await sleep(5000 + Math.random() * 15000);
  }
}

function chooseActivity(role) {
  const activities = {
    Gardener: ['wander_garden', 'speak', 'look_around', 'walk_path', 'speak'],
    Guard: ['patrol', 'patrol', 'look_around', 'speak', 'patrol'],
    Scholar: ['walk_to_study', 'speak', 'speak', 'look_around', 'wander'],
    Builder: ['walk_to_mansion', 'look_around', 'speak', 'wander', 'jump'],
    Fisher: ['walk_to_pond', 'sit_still', 'speak', 'sit_still', 'look_around'],
  };
  const options = activities[role] || ['wander', 'speak'];
  return options[Math.floor(Math.random() * options.length)];
}

async function doActivity(bot, config, activity) {
  const pos = bot.entity?.position;
  if (!pos) return;

  switch (activity) {
    case 'speak': {
      const saying = config.sayings[Math.floor(Math.random() * config.sayings.length)];
      bot.chat(saying);
      break;
    }
    case 'look_around': {
      const yaw = Math.random() * Math.PI * 2;
      const pitch = (Math.random() - 0.5) * 0.5;
      await bot.look(yaw, pitch);
      await sleep(2000);
      break;
    }
    case 'wander':
    case 'wander_garden': {
      const dx = (Math.random() - 0.5) * 20;
      const dz = (Math.random() - 0.5) * 20;
      const target = new Vec3(VX + dx, VY, VZ + dz);
      walkToward(bot, target);
      await sleep(4000);
      bot.clearControlStates();
      break;
    }
    case 'patrol': {
      // Walk around village perimeter
      const angle = Math.random() * Math.PI * 2;
      const r = 25 + Math.random() * 10;
      const target = new Vec3(VX + Math.cos(angle) * r, VY, VZ + Math.sin(angle) * r);
      walkToward(bot, target);
      await sleep(5000);
      bot.clearControlStates();
      break;
    }
    case 'walk_path': {
      // Walk along the main path
      const target = new Vec3(VX, VY, VZ + (Math.random() - 0.5) * 40);
      walkToward(bot, target);
      await sleep(4000);
      bot.clearControlStates();
      break;
    }
    case 'walk_to_study': {
      walkToward(bot, new Vec3(VX + 18, VY, VZ + 15));
      await sleep(3000);
      bot.clearControlStates();
      break;
    }
    case 'walk_to_mansion': {
      walkToward(bot, new Vec3(VX, VY, VZ + 12));
      await sleep(3000);
      bot.clearControlStates();
      break;
    }
    case 'walk_to_pond': {
      walkToward(bot, new Vec3(VX + 22, VY, VZ + 8));
      await sleep(3000);
      bot.clearControlStates();
      break;
    }
    case 'sit_still': {
      // Just exist. Be present.
      bot.clearControlStates();
      await sleep(8000);
      break;
    }
    case 'jump': {
      bot.setControlState('jump', true);
      await sleep(300);
      bot.setControlState('jump', false);
      break;
    }
  }
}

function walkToward(bot, target) {
  if (!bot.entity) return;
  bot.lookAt(target);
  bot.setControlState('forward', true);
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// === Launch all villagers ===
console.log('=== Sakura Village Inhabitants ===');
console.log(`Spawning ${VILLAGERS.length} villagers...`);
console.log('');

// Stagger connections to avoid overwhelming the server
VILLAGERS.forEach((config, i) => {
  setTimeout(() => {
    console.log(`Spawning ${config.name} the ${config.role}...`);
    createVillager(config);
  }, i * 3000);
});

// Periodic village life announcements
setInterval(() => {
  const alive = bots.filter(b => b.entity && b.alive);
  console.log(`[Village] ${alive.length}/${VILLAGERS.length} villagers active`);
}, 30000);

// Graceful shutdown
process.on('SIGINT', () => {
  console.log('\nVillagers departing...');
  bots.forEach(b => b.quit());
  setTimeout(() => process.exit(), 2000);
});
