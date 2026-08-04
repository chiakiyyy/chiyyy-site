<?php
/**
 * 桑原司法書士事務所 — Lightning 子テーマ
 *
 * @package kuwabara-shoshi
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}


/* ==========================================================================
   スタイルシート読み込み
   ========================================================================== */

function kuwabara_shoshi_enqueue_styles() {

	$style_path = get_stylesheet_directory() . '/style.css';

	wp_enqueue_style(
		'kuwabara-shoshi-style',
		get_stylesheet_directory_uri() . '/style.css',
		array(),
		file_exists( $style_path ) ? filemtime( $style_path ) : '1.0.0'
	);
}
add_action( 'wp_enqueue_scripts', 'kuwabara_shoshi_enqueue_styles', 20 );


/* ==========================================================================
   フッター コピーライト
   --------------------------------------------------------------------------
   本番（BizVektor 子テーマ footer.php）の表記を再現する。
     Copyright © 桑原司法書士事務所 All Rights Reserved.
   ========================================================================== */

function kuwabara_shoshi_footer_copyright( $copyright ) {

	$site_url  = esc_url( home_url( '/' ) );
	$site_name = '桑原司法書士事務所';

	$copyright  = '<p class="copyright">';
	$copyright .= 'Copyright &copy; ';
	$copyright .= '<a href="' . $site_url . '">' . esc_html( $site_name ) . '</a>';
	$copyright .= ' All Rights Reserved.';
	$copyright .= '</p>';

	return $copyright;
}
add_filter( 'lightning_footerCopyRightCustom', 'kuwabara_shoshi_footer_copyright' );

function kuwabara_shoshi_footer_powered( $powered ) {
	return '';
}
add_filter( 'lightning_footerPoweredCustom', 'kuwabara_shoshi_footer_powered' );


/* ==========================================================================
   ヘッダー 連絡先表示
   --------------------------------------------------------------------------
   旧サイト（BizVektor）でヘッダー右上に表示されていた連絡先を再現する。

   使用フック: lightning_site_header_logo_after
   表示値は ExUnit → Main setting → Contact Information から取得する。
   ========================================================================== */

function kw_header_contact() {

	$options = get_option( 'vkExUnit_contact' );

	$message = isset( $options['contact_txt'] ) ? $options['contact_txt'] : '';
	$tel     = isset( $options['tel_number'] ) ? $options['tel_number'] : '';
	$time    = isset( $options['contact_time'] ) ? $options['contact_time'] : '';

	if ( ! $message && ! $tel && ! $time ) {
		return;
	}
	?>
	<div class="kw-header-contact">
		<?php if ( $message ) : ?>
			<p class="kw-header-contact__message"><?php echo esc_html( $message ); ?></p>
		<?php endif; ?>

		<?php if ( $tel ) : ?>
			<p class="kw-header-contact__tel">
				<a href="tel:<?php echo esc_attr( preg_replace( '/[^0-9+]/', '', $tel ) ); ?>">
					TEL <?php echo esc_html( $tel ); ?>
				</a>
			</p>
		<?php endif; ?>

		<?php if ( $time ) : ?>
			<p class="kw-header-contact__time"><?php echo esc_html( $time ); ?></p>
		<?php endif; ?>
	</div>
	<?php
}
add_action( 'lightning_site_header_logo_after', 'kw_header_contact' );


/* ==========================================================================
   ウィジェット見出しタグを h2 に統一
   --------------------------------------------------------------------------
   Lightning のサイドバーウィジェット見出しは、デフォルトで <h2> が出力される
   ことが多いが、プラグインや設定によって <h3>/<h4> になる場合がある。
   style.css の .sub-section .sub-section-title セレクタは h2 を基準としているため、
   ここで h2 に統一する。

   ※ Lightning 本体の設定（カスタマイザー → ウィジェット見出しタグ）で
     h2 が選択されている場合は、この関数は実質無効（二重登録になるが無害）。
   ========================================================================== */

function kuwabara_shoshi_widget_title_tag( $params ) {
	if ( isset( $params[0]['before_title'] ) ) {
		$params[0]['before_title'] = '<h2 class="widget-title sub-section-title">';
		$params[0]['after_title']  = '</h2>';
	}
	return $params;
}
add_filter( 'dynamic_sidebar_params', 'kuwabara_shoshi_widget_title_tag' );


/* ==========================================================================
   お知らせ一覧 ショートコード [kw_info_list]
   --------------------------------------------------------------------------
   BizVektor がテーマ側で自動出力していた TOPページのお知らせ一覧を再現する。

   使い方:
     [kw_info_list]
     [kw_info_list count="3"]
     [kw_info_list heading=""]   ← 見出し非表示

   カスタム投稿タイプ「info（お知らせ）」を対象とする。
   ========================================================================== */

function kw_info_list_shortcode( $atts ) {

	$atts = shortcode_atts(
		array(
			'count'   => 5,
			'heading' => 'お知らせ',
			'rss'     => 'yes',
			'archive' => 'yes',
		),
		$atts,
		'kw_info_list'
	);

	$query = new WP_Query(
		array(
			'post_type'           => 'info',
			'posts_per_page'      => (int) $atts['count'],
			'post_status'         => 'publish',
			'ignore_sticky_posts' => true,
			'no_found_rows'       => true,
		)
	);

	if ( ! $query->have_posts() ) {
		return '';
	}

	ob_start();
	?>
	<div class="kw-info">

		<?php if ( '' !== $atts['heading'] || 'yes' === $atts['rss'] ) : ?>
		<div class="kw-info__head">
			<?php if ( '' !== $atts['heading'] ) : ?>
				<h2 class="kw-info__heading"><?php echo esc_html( $atts['heading'] ); ?></h2>
			<?php endif; ?>

			<?php if ( 'yes' === $atts['rss'] ) : ?>
				<a class="kw-info__rss"
				   href="<?php echo esc_url( get_post_type_archive_feed_link( 'info' ) ); ?>">RSS</a>
			<?php endif; ?>
		</div>
		<?php endif; ?>

		<ul class="kw-info__list">
			<?php
			while ( $query->have_posts() ) :
				$query->the_post();
				?>
				<li class="kw-info__item">
					<h3 class="kw-info__item-title">
						<a href="<?php the_permalink(); ?>"><?php the_title(); ?></a>
					</h3>

					<p class="kw-info__date">
						<time datetime="<?php echo esc_attr( get_the_date( 'c' ) ); ?>">
							<?php echo esc_html( get_the_date() ); ?>
						</time>
					</p>

					<?php $excerpt = get_the_excerpt(); ?>
					<?php if ( $excerpt ) : ?>
						<p class="kw-info__excerpt"><?php echo esc_html( $excerpt ); ?></p>
					<?php endif; ?>

					<p class="kw-info__more">
						<a href="<?php the_permalink(); ?>">この記事を読む</a>
					</p>
				</li>
				<?php
			endwhile;
			wp_reset_postdata();
			?>
		</ul>

		<?php if ( 'yes' === $atts['archive'] ) : ?>
			<p class="kw-info__archive">
				<a href="<?php echo esc_url( get_post_type_archive_link( 'info' ) ); ?>">お知らせ一覧</a>
			</p>
		<?php endif; ?>

	</div>
	<?php
	return ob_get_clean();
}
add_shortcode( 'kw_info_list', 'kw_info_list_shortcode' );
