<?php

//
// Interface to chat_stats, for generating reports on buddy activity
// (c) 2013 Carlos E. Torchia <ctorchia87@gmail.com>
// Licensed under GPLv2, no warranty.
//

$PYTHONPATH = 'PYTHONPATH=~/lib/pychartdir';

exec($PYTHONPATH . ' ./pychatstats get_usernames -d log', $usernames);

if ( !isset( $_GET[ 'username' ] ) && !isset( $_GET[ 'start_date' ] ) && !isset( $_GET[ 'end_date' ] ) ) {
    ?>
    <html>
    <head>
    <title>Chat Stats</title>
    </head>
    <body>
    <h2>Chat User Availability Charts</h2>
    <p>Select a user:</p>
    <ol>
    <?php
    foreach ( $usernames as $username ) {
        ?>
        <li><a href="./?username=<?= $username ?>"><?= $username ?></a>
            <a href="./?username=<?= $username ?>&start_date=<?= date('Y-m-d') ?>">today</a>,
            <a href="./?username=<?= $username ?>&start_date=<?= date('Y-m-d', strtotime('-1 day')) ?>&end_date=<?= date('Y-m-d') ?>">yesterday</a>,
            <a href="./?username=<?= $username ?>&start_date=<?= date('Y-m-d', strtotime('last sunday')) ?>&end_date=<?= date('Y-m-d', strtotime('next saturday')) ?>">this week</a>
            <a href="./?username=<?= $username ?>&start_date=<?= date('Y-m-d', strtotime('last sunday - 1 week')) ?>&end_date=<?= date('Y-m-d', strtotime('last saturday')) ?>">last week</a>
            <a href="./?username=<?= $username ?>&start_date=<?= date('Y-m-d', strtotime('-30 days + 1 day')) ?>">last 30 days</a>
        <?php
    }
    ?>
    </ol>
    </body>
    </html>
    <?php
}
else if ( isset( $_GET[ 'username' ] ) ) {
    # Build the command line for generating the chart
    $command_line = 'PYTHONPATH=~/lib/pychartdir ./pychatstats chart_by_hour -d log';
    $command_line .= ' -u ' . escapeshellarg( $_GET[ 'username' ] );

    if ( isset( $_GET[ 'start_date' ] ) ) {
        $command_line .= ' -s ' . escapeshellarg( $_GET[ 'start_date' ] );
    }

    if ( isset( $_GET[ 'end_date' ] ) ) {
        $command_line .= ' -e ' . escapeshellarg( $_GET[ 'end_date' ] );
    }

    # Run the command, output image to browser
    header( 'Content-Type: image/png' );
    passthru( $PYTHONPATH . ' ' . $command_line );
}
