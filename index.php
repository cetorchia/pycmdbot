<?php

//
// Interface to chat_stats, for generating reports on buddy activity
// (c) 2013 Carlos E. Torchia <ctorchia87@gmail.com>
// Licensed under GPLv2, no warranty.
//

require_once( 'authenticate.php' );

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

    $today = date( 'Y-m-d' );
    $yesterday = date( 'Y-m-d', strtotime( '-1 day' ) );
    $this_week_start = date( 'Y-m-d', strtotime( 'this saturday - 6 days' ) );
    $this_week_end = date( 'Y-m-d', strtotime( 'this saturday' ) );
    $last_week_start = date( 'Y-m-d', strtotime( 'this saturday - 6 days - 1 week' ) );
    $last_week_end = date( 'Y-m-d', strtotime( 'this saturday - 1 week' ) );
    $one_month_ago = date( 'Y-m-d', strtotime( '-30 days + 1 day' ) );

    // Loop through each username and display links to their
    // activity charts.
    foreach ( $usernames as $username ) {
        ?>
        <li><b><?= $username ?>:</b>
            <a href="./?username=<?= $username ?>">all time</a> &nbsp;
            <a href="./?username=<?= $username ?>&start_date=<?= $today ?>">today</a> &nbsp;
            <a href="./?username=<?= $username ?>&start_date=<?= $yesterday ?>&end_date=<?= $yesterday ?>">yesterday</a> &nbsp;
            <a href="./?username=<?= $username ?>&start_date=<?= $this_week_start ?>&end_date=<?= $this_week_end ?>">this week</a> &nbsp;
            <a href="./?username=<?= $username ?>&start_date=<?= $last_week_start ?>&end_date=<?= $last_week_end ?>">last week</a> &nbsp;
            <a href="./?username=<?= $username ?>&start_date=<?= $one_month_ago ?>">last 30 days</a> &nbsp;
        <?php
    }
    ?>
    </ol>
    <p>Most recent timestamp:
        <?php
        passthru( 'date +"%F %T" -d @$(cat log/* | tail -n 1 | awk -F . \'{ print $1 }\')' );
        ?>
    </p>
    </body>
    </html>
    <?php
}
else if ( isset( $_GET[ 'username' ] ) ) {
    # Build the command line for generating the chart
    $command_line = './pychatstats chart_by_hour -d log';
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
