#!/usr/bin/python3

import re
import json
from absl import app, flags
from neo4j import GraphDatabase

FLAGS = flags.FLAGS

def add_options():
  flags.DEFINE_string('input', default = None, help = 'path to input')
  flags.DEFINE_string('host', default = 'bolt://localhost:7687', help = 'host')
  flags.DEFINE_string('user', default = 'neo4j', help = 'username')
  flags.DEFINE_string('password', default = 'neo4j', help = 'password')
  flags.DEFINE_string('db', default = 'test2', help = 'database')

def main(unused_argv):
  entities = list()
  relations = list()
  events = list()
  attributes = list()
  with open(FLAGS.input, 'r') as f:
    for line in f.readlines():
      if len(line.strip()) == 0: continue
      delimiters = r'[ \t]'
      tokens = re.split(delimiters, line.strip())
      if line.startswith('T'):
        # entity
        #assert len(tokens) == 5, f"line: {line} failed assertion"
        ent_id = tokens[0]
        ent_type = tokens[1]
        start = tokens[2]
        end = tokens[3]
        text = ' '.join(tokens[4:])
        entities.append({'id': ent_id, 'type': ent_type, 'start': start, 'end': end, 'text': text})
      elif line.startswith('E'):
        # event
        event = {'id': tokens[0], 'roles': list()}
        for i in range(1, len(tokens)):
          role, ent_id = tokens[i].split(':')
          event['roles'].append({'role': role, 'id': ent_id})
        events.append(event)
      elif line.startswith('R'):
        # relation
        assert len(tokens) == 4, f"line: {line} failed assertion"
        rel_id = tokens[0]
        rel_type = tokens[1]
        head_ent_id = tokens[2].split(':')[1]
        tail_ent_id = tokens[3].split(':')[1]
        relations.append({'id': rel_id, 'type': rel_type, 'head': head_ent_id, 'tail': tail_ent_id})
      elif line.startswith('A'):
        # attribute
        assert len(tokens) == 3
        att_id = tokens[0]
        att_type = tokens[1]
        event_id = tokens[2]
        attributes.append({'id': att_id, 'type': att_type, 'event': event_id})
      else:
        raise Exception('unknown type!')
  with open('all.json', 'w') as f:
    f.write(json.dumps({'entities': entities, 'relations': relations, 'events': events, 'attributes': attributes}, indent = 2, ensure_ascii = False))
  driver = GraphDatabase.driver(FLAGS.host, auth = (FLAGS.user, FLAGS.password))
  for entity in entities:
    records, summary, keys = driver.execute_query('merge (a: %s {id: $id, name: $name, start: $start, end: $end}) return a;' % entity['type'], id = entity['id'], name = entity['text'], start = entity['start'], end = entity['end'], database_ = FLAGS.db)
  for event in events:
    if len(list(filter(lambda x: x['role'] == 'SOP', event['roles']))):
      records, summary, keys = driver.execute_query('merge (a: SOP_Event {id: $id}) return a;', id = event['id'], database_ = FLAGS.db)
    else:
      records, summary, keys = driver.execute_query('merge (a: CND_Event {id: $id}) return a;', id = event['id'], database_ = FLAGS.db)
    for role in event['roles']:
        records, summary, keys = driver.execute_query('match (a {id: $id}), (b {id: $ent_id}) merge (a)-[r:%s]->(b);' % role['role'].replace('-','_'), id = event['id'], ent_id = role['id'], database_ = FLAGS.db)
  for attribute in attributes:
    records, summary, keys = driver.execute_query('merge (a: Attribute {id: $id, type: $type}) return a;', id = attribute['id'], type = attribute['type'], database_ = FLAGS.db)
    records, summary, keys = driver.execute_query('match (a: Attribute {id: $id}), (b {id: $event_id}) merge (a)-[r:ATTRIBUTE]->(b);', id = attribute['id'], event_id = attribute['event'], database_ = FLAGS.db)
  for relation in relations:
    records, summary, keys = driver.execute_query('match (a {id: $id1}), (b {id: $id2}) merge (a)-[r:%s]->(b);' % relation["type"].replace('-','_'), id1 = relation['head'], id2 = relation['tail'],  database_ = FLAGS.db)

if __name__ == "__main__":
  add_options()
  app.run(main)

