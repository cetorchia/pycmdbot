<?php

//
// Interface to chat_stats, for generating reports on buddy activity
// (c) 2013 Carlos E. Torchia <ctorchia87@gmail.com>
// Licensed under GPLv2, no warranty.
//

$PYTHONPATH = 'PYTHONPATH=~/lib/pychartdir';

exec($PYTHONPATH . ' ./pychatstats get_usernames -d log', $usernames);

if ( !isset( $_GET[ 'username' ] ) && !isset( $_GET[ 'period' ] ) ) {
    ?>
    <html>
    <head>
    <title>Chat Stats</title>
    </head>
    <body>
    <h2>Chat User Availability Charts</h2>
    <p>Select a user:</p>
    <ul>
    <?php
    foreach ( $usernames as $username ) {
        ?>
        <li><a href="./?username=<?= $username ?>"><?= $username ?></a>
            <a href="./?username=<?= $username ?>&period=day">last day</a>,
            <a href="./?username=<?= $username ?>&period=week">last week</a>
        <?php
    }
    ?>
    </ul>
    </body>
    </html>
    <?php
}
else if ( isset( $_GET[ 'username' ] ) ) {
    # Build the command line for generating the chart
    $command_line = 'PYTHONPATH=~/lib/pychartdir ./pychatstats chart_by_hour -d log -u ';
    $command_line .= escapeshellarg( $_GET[ 'username' ] );
    if ( 'day' == $_GET[ 'period' ] ) {
        $command_line .= ' -l 1';
    }
    else if ( 'week' == $_GET[ 'period' ] ) {
        $command_line .= ' -l 7';
    }

    # Run the command, output image to browser
    header( 'Content-Type: image/png' );
    passthru( $PYTHONPATH . ' ' . $command_line );
}
