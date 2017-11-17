import tensorflow as tf


def inference(spectrogram,
              num_hidden,
              seq_length,
              n_syllables,
              batch_size=11,
              input_vec_size=513):
    """inference graph for 'inferring' labels of birdsong syllables
    hybrid convolutional neural net with bidirectional LSTM layer

    Arguments
    ---------
    spectrogram : tf.placeholder
        placeholder for training data.
        gets reshaped to (batch_size, spectrogram width, spectrogram height, 1 channel)
        spectrogram height is the same as "input vec size"
    num_hidden : int
        number of hidden layers in LSTMs
    seq_length : tf.placeholder
        holds sequence length
        equals time_steps * batch_size, where time_steps is defined by user as a constant
    n_syllables : int
        number of syllable types
        used as shape of output
    batch_size : int
        number of items in a batch.
        length of axis 0 of 3-d input array (spectrogram)
        default is 11.
    input_vec_size : int
        length of axis 3 of 3-d input array
        number of frequency bins in spectrogram
        default is 513

    Returns
    -------
    outputs : tensorflow tensor

    logits : tensorflow tensor

    """

    # First convolutional layers
    # Convolutional Layer #1
    conv1 = tf.layers.conv2d(
        inputs=tf.reshape(spectrogram, [batch_size, -1, input_vec_size, 1]),
        filters=32,
        kernel_size=[5, 5],
        padding="same",
        activation=tf.nn.relu)
    # Pooling Layer #1
    pool1 = tf.layers.max_pooling2d(inputs=conv1,
                                    pool_size=[1, 8],
                                    strides=[1, 8])
    # Convolutional Layer #2 and Pooling Layer #2
    conv2 = tf.layers.conv2d(
        inputs=pool1,
        filters=64,
        kernel_size=[5, 5],
        padding="same",
        activation=tf.nn.relu)
    pool2 = tf.layers.max_pooling2d(inputs=conv2,
                                    pool_size=[1, 8],
                                    strides=[1, 8])
    # Second the dynamic bi-directional LSTM
    lstm_f1 = tf.contrib.rnn.BasicLSTMCell(num_hidden, forget_bias=1.0, state_is_tuple=True, reuse=None)
    lstm_b1 = tf.contrib.rnn.BasicLSTMCell(num_hidden, forget_bias=1.0, state_is_tuple=True, reuse=None)
    outputs, _states = tf.nn.bidirectional_dynamic_rnn(lstm_f1,
                                                       lstm_b1,
                                                       tf.reshape(pool2, [batch_size, -1, num_hidden]),
                                                       time_major=False,
                                                       dtype=tf.float32,
                                                       sequence_length=seq_length)

    # Third, projection on the number of syllables creates logits time_steps
    with tf.name_scope('Projection'):
        W_f = tf.Variable(tf.random_normal([num_hidden, n_syllables]))
        W_b = tf.Variable(tf.random_normal([num_hidden, n_syllables]))
        bias = tf.Variable(tf.random_normal([n_syllables]))

    expr1 = tf.unstack(outputs[0],
                       axis=0,
                       num=batch_size)
    expr2 = tf.unstack(outputs[1],
                       axis=0,
                       num=batch_size)
    logits = tf.concat([tf.matmul(ex1, W_f) + bias + tf.matmul(ex2, W_b)
                        for ex1, ex2 in zip(expr1, expr2)],
                       0)
    return logits, outputs

xentropy = tf.nn.sparse_softmax_cross_entropy_with_logits


def train(logits, lbls, rate, batch_size):
    """training graph for label inference graph.
    Calculates cross entropy and loss function

    Parameters
    ----------
    logits : tensorflow tensor

    lbls: int
        labels
    rate:
     learning rate
    """

    xentropy_layer = xentropy(logits=logits,
                              labels=tf.concat(tf.unstack(lbls,
                                                          axis=0,
                                                          num=batch_size),
                                               0),
                              name='xentropy')
    cost = tf.reduce_mean(xentropy_layer, name='cost')
    optimizer = tf.train.AdamOptimizer(learning_rate=rate)
    global_step = tf.Variable(0, name='global_step', trainable=False)
    train_op = optimizer.minimize(cost, global_step=global_step)
    return train_op, cost


def get_full_graph(input_vec_size=513, num_hidden=512, n_syllables=16,
                   learning_rate=0.001, batch_size=11):

    full_graph = tf.Graph()
    with full_graph.as_default():
            # Generate placeholders for the spectrograms and labels.
            # X holds spectrograms batch_size,time_steps
            X = tf.placeholder("float",
                               [None,
                                None,
                                input_vec_size],
                               name="Xdata")
            Y = tf.placeholder("int32",
                               [None, None],
                               name="Ylabels")  # holds labels batch_size
            lng = tf.placeholder("int32",
                                 name="nSteps")  # holds the sequence length
            tf.add_to_collection("specs", X)  # Remember this Op.
            tf.add_to_collection("labels", Y)  # Remember this Op.
            tf.add_to_collection("lng", lng)  # Remember this Op.
            # Build a Graph that computes predictions from the inference model.
            logits, outputs = inference(X,
                                        num_hidden,
                                        lng,
                                        n_syllables,
                                        batch_size,
                                        input_vec_size)  # lstm_size
            tf.add_to_collection("logits", logits)  # Remember this Op.

            # Add to the Graph the Ops that calculate and apply gradients.
            train_op, cost = train(logits, Y, learning_rate, batch_size)

            init = tf.global_variables_initializer()

            # Create a saver for writing training checkpoints.
            saver = tf.train.Saver(max_to_keep=10)

    return (full_graph, train_op, cost,
            init, saver, logits, X, Y, lng)
