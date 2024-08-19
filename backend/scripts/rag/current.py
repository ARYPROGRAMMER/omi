import uuid
from datetime import datetime
from typing import Dict, Tuple

from _shared import *
from models.chat import Message
from utils.llm import determine_requires_context


def _get_mesage(text: str, sender: str):
    return Message(id=str(uuid.uuid4()), text=text, created_at=datetime.utcnow(), sender=sender, type='text')


conversation = [
    _get_mesage('Hi', 'human'),
    _get_mesage('Hi, how can I help you today?', 'ai'),
    _get_mesage('Have I learned about business, life and regrets?', 'human'),
]


def get_data(uid: str, topics: List[str], top_k: int = 1000) -> Dict[str, List]:
    memories = get_memories(uid)
    memories = {memory['id']: memory for memory in memories}
    all_vectors = query_vectors('', uid, k=top_k)
    all_vectors = {
        mid: {
            'vector': vector,
            'topics': []
        } for mid, vector in all_vectors
    }
    for topic in topics:
        vectors = query_vectors(topic, uid, k=5)
        for mid, vector in vectors:
            if mid in all_vectors:
                all_vectors[mid]['topics'].append(topic)

    result = {}
    for mid, data in all_vectors.items():
        memory = memories.get(mid)
        if not memory:
            continue
        result[mid] = {
            'title': memory['structured']['title'],
            'vector': data['vector'],
            'topics': data['topics']
        }

    return result


def get_markers(data, data_points, color, name, show_top=None):
    if show_top:
        data = list(data.items())[:show_top]
        data_points = data_points[:show_top]
    else:
        data = list(data.items())

    return go.Scatter(
        x=data_points[:, 0],
        y=data_points[:, 1],
        mode='markers',
        marker=dict(size=8, opacity=0.7, color=color),
        text=[f"Title: {item[1]['title']}<br>Topics: {', '.join(item[1]['topics'])}" for item in data],
        hoverinfo='text',
        name=name
    )


def visualize():
    uid = 'mLHEZwhBj0PLQHmCLZNLXQwcJXg2'

    context: Tuple = determine_requires_context(conversation)
    if not context or not context[0]:
        print('No context is needed')
        return
    topics = context[0]
    # topics = ['Business', 'Entrepreneurship', 'Failures']

    data = get_data(uid, topics)
    all_embeddings = np.array([item['vector'] for item in data.values()])

    topic_embeddings = [openai_embeddings.embed_query(topic) for topic in topics]
    all_embeddings = np.vstack([all_embeddings] + topic_embeddings)

    umap_transform = umap.UMAP(n_components=2, random_state=0, transform_seed=0)
    umap_embeddings = umap_transform.fit_transform(all_embeddings)

    data_points = umap_embeddings[:-len(topics)]
    topic_points = umap_embeddings[-len(topics):]

    fig = make_subplots(rows=1, cols=1)

    colors = ['blue', 'green', 'orange', 'purple', 'cyan', 'magenta']

    # Add all vectors
    fig.add_trace(get_markers(data, data_points, 'gray', 'All Vectors'))

    # Add vectors for each topic
    for i, topic in enumerate(topics):
        color = colors[i % len(colors)]
        topic_data = {mid: item for mid, item in data.items() if topic in item['topics']}
        topic_data_points = np.array([data_points[list(data.keys()).index(mid)] for mid in topic_data.keys()])

        fig.add_trace(get_markers(topic_data, topic_data_points, color, f'Top 5 - {topic}'))
        fig.add_trace(get_query_marker(topic_points[i], topic))

    fig.update_layout(
        title='Embedding Visualization for Multiple Topics',
        xaxis_title='UMAP Dimension 1',
        yaxis_title='UMAP Dimension 2',
        width=1000,
        height=800,
        showlegend=True,
        hovermode='closest'
    )

    generate_html_visualization(fig, file_name='embedding_visualization_multi_topic.html')


if __name__ == '__main__':
    visualize()